import logging
from flask import Blueprint, render_template, request
from CourseScheduling.blueprints.schedule.models import Course, Requirement
from CourseScheduling.blueprints.schedule import dgw_data
import lib.CourseSchedulingAlgorithm as cs

schedule = Blueprint('schedule', __name__, template_folder='templates')

@schedule.route('/')
def schedule_home():
    return render_template('schedule/input.html')


@schedule.route('/test')
def test():
    output = []
    for course in Course.objects(dept='COMPSCI'):
        output.append(course.name)
    return str(output)

@schedule.route('/saveme')
def saveme():
    return render_template('schedule/saveme.html')

@schedule.route('/launch')
def launch():
    cookie = request.args.get('cookie', '')
    d = dgw_data.data(cookie)
    std = d.fetch_student_id()
    d.fetch_student_detail()
    student = d.getDict()
    d.fetch_xml()
    return render_template('schedule/info.html', student=student)

@schedule.route('/output', methods=['POST', 'GET'])
def schedule_output():

    # user info should be private 
    # also user info could be too large for GET request
    if request.method != 'POST':
      return "Naughty boy. Maybe next time."

    ############### fake input ###################
    
    # input will be provided by POST request. 
    # config upper standing units
    upper_units = 90
    # start quarter 
    startQ = 0
    # units applied
    applied_units = 0
    # set of courses taken
    taken = {'MATH1B'}
    # width setting
    max_widths = {0: 13, 'else': 16}
    # avoid
    avoid = {'COMPSCI141'}
    # requirements 
    req = {"University", "GEI", "GEII", "GEIII", "GEIV",
              "GEV", "GEVI", "GEVII", "GEVIII", "CS-Lower-division", "CS-Upper-division",
              "Intelligent Systems"}

    ##############################################

    # 现在把数据库的data拿出来 然后一个个建立 lib.CourseSchedulingAlgorithm.Course 然后装进Graph (jenny的example是这么做的).
    # 未来优化：因为db里已经有一份copy了，所以两倍的memory。之后应该要改一下。

    # ！！！新修改了此处 从直接在这里query db的东西 改成调用dbHelper 里面的function

    # new MODEL applied
    G, R, R_detail = dict(), dict(), dict()
    for r in req:
        R[r] = list()
        R_detail[r] = list()
        for subr in Requirement.objects(name=r).first().sub_reqs:
            c_set = set()
            R[r].append(subr.req_num)
            for c in subr.req_list:
                c_name = c.dept + c.cid
                c_set.add(c_name)
                G[c_name] = cs.Course(name=c.name, units=c.units, quarter_codes=c.quarters, 
                    prereq=c.prereq, is_upper_only=c.upperOnly)
            R_detail[r].append(c_set)


    #########################

    # update requirement table based on the taken information
    cs.update_requirements(R_detail, R, taken)
    # construct CourseGraph. graph is labeled after init
    graph = cs.CourseGraph(G, r_detail=R_detail, R=R, avoid=avoid, taken=taken)
    # construct Schedule with width func requirements
    L = cs.Schedule(widths=max_widths)
    # construct the scheduling class
    generator = cs.Scheduling(start_q=startQ)
    # get the best schedule when the upper bound ranges from 0 to 10, inclusive.
    L, best_u, best_r = generator.get_best_schedule(graph, L, R, 0, 10)

    max_row_length = max(len(row) for row in L.L)

    # the parameters for render_template will be provided by CourseSchedulingAlgorithm:
    #   1,  L : best schedule generated by the algorithm
    #   2,  max_row_length : the max length of a row in this schedule

    return render_template('schedule/output.html',
                           schedule=L, row_length=max_row_length)

