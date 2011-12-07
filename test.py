#! /usr/bin/python
# encoding:utf-8
from grab import Grab
import sqlite3
import re
import time


post_data = (
    ('p1',1234),
    ('p2',123456),
    ('p_test',6),
    ('p_try_number',1),
    ('p_submit',"y"),
)

domen = r'http://shelly.ksu.ru/e-ksu/'
url = domen + 'student_auditorium.testbody'
url_finish = domen + 'student_auditorium.finish_test?p1=%s&p2=%s&p_test=%s&p_try_number=1'%(post_data[0][1],post_data[1][1],post_data[2][1])
url_begin = domen + 'student_personal.study_tasks?p1=%s&p2=%s&p_tp=i&p_discipline=23&p_id=%s&p_test_type=1'%(post_data[0][1],post_data[1][1],post_data[2][1])
url_start = domen + 'student_auditorium.start_test_script'

g = Grab()
conn = sqlite3.connect('db')

def get_answer(question_id):
    c = conn.cursor()
    c.execute('select * from answers where is_right=1 and question=?',(question_id,))
    res = []
    order = []
    for row in c:
        res.append(row[0])
        if type(row[3]) != int:
            return [('p_answer',row[5])]
        if row[4] and row[4] != 'NULL\n':
            order.append(row[4])
    if len(res) > 1:
        answer = []
        if order: res = order
        for i in res: answer.append(('p_answer_plus',i))
        return answer
    else:
        return [('p_answer',res[0])]

def find_question(question_no):
    c = conn.cursor()
    try:
        t = g.search_rex(re.compile('name="p_answer.*value="(\d+)',re.U)).group(1)
        c.execute('select * from answers where id=?',(t,))
        for row in c: return row[1]
    except:
        t = g.css_text('form td[align=left]')
        c.execute('select * from questions where txt like ?',('%' + t.strip()[:50] + '%',))
        for row in c: return row[0]
    raise Exception("Question ID not found for test #%s, question #%s"%(post_data[2][1],question_no))
    
def perform_response(question_no):
    data = get_answer(find_question(question_no))
    data.extend(post_data)
    data.extend([('p_quest',question_no),('p_submit',"n")])
    g.setup(post=data)
    g.go(url)
    if g.search(u'Решение:'):
        g.setup(post=[post_data[0],post_data[1],post_data[2],post_data[3],('p_quest',question_no + 1)])
        g.go(url)
    
def load():
    import codecs
    c = conn.cursor()
    c.execute('''create table if not exists answers(
        id int primary key asc,
        question int,
        is_right int,
        show_order int,
        right_order int,
        txt text
    )''')
    for line in codecs.open('/home/answers',encoding='utf-8'):
        arr = line.split(';')
        c.execute('insert into answers values (?,?,?,?,?,?)',
            (arr[0],arr[1],int(arr[4] == '"y"'),arr[5],arr[6],arr[2][1:-1]))
    c.execute('''create table if not exists questions(
        id int primary key asc,
        txt text
    )''')
    for line in codecs.open('/home/questions',encoding='utf-8'):
        arr = line.split(';')
        try:
            idt = int(arr[0])
            c.execute('insert into questions values (?,?)',(idt,arr[1]))
        except:
            pass
    conn.commit()

g.go(url_begin) # it's seems like not really required
g.setup(post=[post_data[0],post_data[1],post_data[2],('p_test_type',1),('p_action','n')])
g.go(url_start)

for i in xrange(20):
    print "Question #"+str(i+1)
    perform_response(i+1)
    print "Sleeping"
    time.sleep(30)
    
g.go(url_finish)
