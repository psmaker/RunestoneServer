from os import path
import os
import shutil
import sys
from sphinx.application import Sphinx

@auth.requires(lambda: verifyInstructorStatus(auth.user.course_name, auth.user), requires_login=True)
def admin():
	course = db(db.courses.id == auth.user.course_id).select().first()
	# get all assignments
	assignments = db(db.assignments.course == course.id).select()
	return dict(
		assignments = assignments,
		)

@auth.requires(lambda: verifyInstructorStatus(auth.user.course_name, auth.user), requires_login=True)
def create():
	course = db(db.courses.id == auth.user.course_id).select().first()
	assignment = db(db.assignments.id == request.get_vars.id).select().first()
	db.assignments.grade_type.widget = SQLFORM.widgets.radio.widget
	form = SQLFORM(db.assignments, assignment,
	    showid = False,
	    fields=['name','points','query','grade_type','threshold'],
	    keepvalues = True,
	    formstyle='table3cols',
	    )
	form.vars.course = course.id
	if form.process().accepted:
		session.flash = 'form accepted'
		return redirect(URL('assignments','update')+'?id=%d' % (form.vars.id))
	elif form.errors:
		response.flash = 'form has errors'
	return dict(
		form = form,
		)

@auth.requires(lambda: verifyInstructorStatus(auth.user.course_name, auth.user), requires_login=True)
def update():
	course = db(db.courses.id == auth.user.course_id).select().first()
	assignment = db(db.assignments.id == request.get_vars.id).select().first()

	db.assignments.grade_type.widget = SQLFORM.widgets.radio.widget
	form = SQLFORM(db.assignments, assignment,
	    showid = False,
	    fields=['name','points','query','grade_type','threshold'],
	    keepvalues = True,
	    formstyle='table3cols',
	    )
	
	form.vars.course = course.id
	if form.process().accepted:
		session.flash = 'form accepted'
		return redirect(URL('assignments','update')+'?id=%d' % (form.vars.id))
	elif form.errors:
		response.flash = 'form has errors'
	new_deadline_form = SQLFORM(db.deadlines,
		showid = False,
		fields=['section','deadline'],
		keepvalues = True,
		formstyle='table3cols',
		)
	new_deadline_form.vars.assignment = assignment
	if new_deadline_form.process().accepted:
		session.flash = 'added new deadline'
	elif new_deadline_form.errors:
		response.flash = 'error adding deadline'

	deadlines = db(db.deadlines.assignment == assignment.id).select()
	delete_deadline_form = FORM()
	for deadline in deadlines:
		deadline_label = "On %s" % (deadline.deadline)
		if deadline.section:
			section = db(db.sections.id == deadline.section).select().first()
			deadline_label = deadline_label + " for %s" % (section.name)
		delete_deadline_form.append(LABEL(
			INPUT(_type="checkbox", _name=deadline.id, _value="delete"),
			deadline_label,
			_class="checkbox"
			))
	delete_deadline_form.append(INPUT(_type="submit"))

	if delete_deadline_form.accepts(request,session):
		for var in delete_deadline_form.vars:
			if delete_deadline_form.vars[var] == "delete":
				db(db.deadlines.id == var).delete()
		session.flash = 'Deleted deadline(s)'
		return redirect(URL('assignments','update')+'?id=%d' % (assignment.id))

	return dict(
		assignment = assignment,
		form = form,
		new_deadline_form = new_deadline_form,
		delete_deadline_form = delete_deadline_form,
		)

@auth.requires(lambda: verifyInstructorStatus(auth.user.course_name, auth.user), requires_login=True)
def grade():
	course = db(db.courses.id == auth.user.course_id).select().first()
	assignment = db(db.assignments.id == request.get_vars.id).select().first()

	count_graded = 0
	for row in db(db.auth_user.course_id == course.id).select():
		assignment.grade(row)
		count_graded += 1
	session.flash = "Graded %d Assignments" % (count_graded)
	return redirect(URL('assignments','admin'))

# Student version of index
def index():
	if 'sid' not in request.vars and verifyInstructorStatus(auth.user.course_name, auth.user):
		return redirect(URL('assignments','admin'))
	if 'sid' not in request.vars:
		return redirect(URL('assignments','index') + 'sid=%d' % (auth.user.id))
	if auth.user.id != request.vars.sid and not verifyInstructorStatus(auth.user.course_name, auth.user):
		return redirect(URL('assignments','index'))
	student = db(db.auth_user.id == request.vars.sid).select().first()
	if not student:
		return redirect(URL('assignments','index'))

	course = db(db.courses.id == auth.user.course_id).select().first()
	assignments = db(db.assignments.id == db.grades.assignment)(db.assignments.course == course.id and db.grades.auth_user == auth.user.id).select()

	return dict(
		assignments = assignments,
		student = student,
		)

def detail():
	course = db(db.courses.id == auth.user.course_id).select().first()
	assignment = db(db.assignments.id == request.vars.id and db.assignments.course == course.id).select().first()
	if not assignment:
		return redirect(URL("assignments","index"))
	user_id = auth.user.id
	if 'sid' in request.vars:
		user_id = request.vars.sid
	user = db(db.auth_user.id == user_id).select().first()
	# Get acid and list
	problems = assignment.problems(user)

	return dict(
		assignment = assignment,
		problems = problems,
		)