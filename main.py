# -*- coding: UTF-8 -*-

import kivy

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from os import listdir
import re
from random import sample

datapath = "./data/"
sm = ScreenManager()

def load_questions(name):

	question_list = []

	with open(datapath + name + '.quiz', 'r') as f:
		for line in f:
			question = re.findall('[^|>]+', line, re.UNICODE)
			
			if len(question) <= 1:
				continue

			question_list.append((question[0], question[1:]))

	return question_list

def save_questions(name, questions):

	with open(datapath + name + '.quiz', 'w') as f:
		for (question, answers) in questions:
			s = question + '>'
			s += answers[0]
			for answer in answers[1:]:
				s += '|' + answer
			s += '\n'
			
			f.write(s)

class QuizChooserWidget(ScrollView):
	def __init__(self, process_chosen, **kwargs):
		super(QuizChooserWidget, self).__init__(**kwargs)
		
		layout = BoxLayout(orientation='vertical', size_hint_y=None, height=400)
		
		quizpaths = listdir(datapath)

		self.names = []

		for path in quizpaths:
			tmplist = re.split('\.quiz', path)

			name = ''
			if (len(tmplist) == 2 and tmplist[1] == ''):
				name = tmplist[0]
			else:
				continue

			layout.add_widget(Button(text=name, on_press=lambda inst: process_chosen(inst.text), size_hint_y=None, height=100))

		layout.add_widget(Button(text='Zurück', on_press=lambda inst: sm.switch_to(MenuScreen()), size_hint_y=None, height=100))

		self.add_widget(layout)

class QuestionScreen(Screen):
	def __init__(self, quiz, **kwargs):
		super(QuestionScreen, self).__init__(**kwargs)
		self.layout = BoxLayout(orientation='vertical')
		self.quiz = quiz
		self.add_widget(self.layout)

	def showQuestion(self, question, score, max_score):
		self.layout.clear_widgets()

		s = 'Score: ' + str(score) + ' von ' + str(max_score)

		self.layout.add_widget(Label(text=s))
		self.layout.add_widget(Label(text=(question[0])))

		for ans in sample(question[1], len(question[1])):
			self.layout.add_widget(Button(text=ans, on_press=lambda inst: self.quiz.answer_is(inst.text)))

class AnswerScreen(Screen):
	def __init__(self, quiz, **kwargs):
		super(AnswerScreen, self).__init__(**kwargs)
		self.layout = BoxLayout(orientation='vertical')
		self.quiz = quiz
		self.add_widget(self.layout)

	def correct(self, question, score, max_score):
		self.layout.clear_widgets()

		self.layout.add_widget(Label(text=question[0] + ':'))
		self.layout.add_widget(Label(text=question[1][0]))
		self.layout.add_widget(Label(text='Die Antwort ist richtig!'))
		self.layout.add_widget(Label(text='Score: ' + str(score) + ' von ' + str(max_score)))

		self.layout.add_widget(Button(text='Weiter', on_press=lambda inst: self.quiz.next()))

	def wrong(self, question, answer, score, max_score):
		self.layout.clear_widgets()

		self.layout.add_widget(Label(text=question[0] + ':'))
		self.layout.add_widget(Label(text=answer))
		self.layout.add_widget(Label(text='Falsche Antwort! Richtig gewesen wäre:'))
		self.layout.add_widget(Label(text=question[1][0]))
		self.layout.add_widget(Label(text='Score: ' + str(score) + ' von ' + str(max_score)))

		self.layout.add_widget(Button(text='Weiter', on_press=lambda inst: self.quiz.next()))

class ResultScreen(Screen):
	def __init__(self, score, max_score, **kwargs):
		super(ResultScreen, self).__init__(**kwargs)

		self.layout = BoxLayout(orientation='vertical')

		self.layout.add_widget(Label(text='Du hast ' + str(score) + ' von ' + str(max_score) + ' Fragen richtig beantwortet!'))
		self.layout.add_widget(Button(text='Zurück', on_press=lambda inst: sm.switch_to(MenuScreen())))

		self.add_widget(self.layout)

class Quiz:
	def __init__(self, name):
		self.questions = load_questions(name)
		self.questions = sample(self.questions, len(self.questions))

		self.score = 0
		self.max_score = 0

		self.qscreen = QuestionScreen(self)
		self.qscreen.showQuestion(self.questions[-1], self.score, self.max_score)

		self.ascreen = AnswerScreen(self)

		sm.switch_to(self.qscreen)

	def answer_is(self, answer):
		question = self.questions.pop()
		self.max_score += 1

		if (answer == question[1][0]):
			self.score += 1
			self.ascreen.correct(question, self.score, self.max_score)
		else:
			self.ascreen.wrong(question, answer, self.score, self.max_score)

		sm.switch_to(self.ascreen)

	def next(self):
		if not self.questions:
			sm.switch_to(ResultScreen(self.score, self.max_score))
		else:
			self.qscreen.showQuestion(self.questions[-1], self.score, self.max_score)
			sm.switch_to(self.qscreen)

class StartQuizScreen(Screen):
	def __init__(self, **kwargs):
		super(StartQuizScreen, self).__init__(**kwargs)

		self.add_widget(QuizChooserWidget(lambda name: Quiz(name), size_hint=(0.8, 1.0)))

class EditorScreen(Screen):
	
	def __init__(self, name, **kwargs):
		super(EditorScreen, self).__init__(**kwargs)
		
		self.name = name
		self.qlist = load_questions(name)

		if not self.qlist:
			self.selected = -1
		else:
			self.selected = 0

		self.qstn_box = TextInput(multiline=True)
		self.answer_list = []

		layout = BoxLayout(orientation='vertical', pos_hint={'center_x': 0.5}, size_hint=(0.8, 1.0))
		btnLayout = BoxLayout(orientation='horizontal', size_hint=(1.0, .1))
		btnLayout.add_widget(Button(text='<--', on_press=lambda inst: self.move(False)))
		btnLayout.add_widget(Button(text='-->', on_press=lambda inst: self.move(True), pos_hint={'center_x': 0.9}))

		layout.add_widget(btnLayout)

		self.qstnLayout = BoxLayout(orientation='vertical', size_hint=(1.0, .6))
		layout.add_widget(self.qstnLayout)
		
		self.show_selected()

		btnLayout2 = BoxLayout(orientation='horizontal', size_hint=(1.0, .1))
		btnLayout2.add_widget(Button(text='Neue Antwort', on_press=lambda inst: self.add_answer()))
		btnLayout2.add_widget(Button(text='Speichern', on_press=lambda inst: self.save()))
		btnLayout2.add_widget(Button(text='Zurück', on_press=lambda inst: self.back()))
		layout.add_widget(btnLayout2)

		self.add_widget(layout)

	def show_selected(self):
		self.qstnLayout.clear_widgets()
		self.answer_list = []

		if (self.selected != -1):
			self.qstn_box.text = self.qlist[self.selected][0]

			if not self.qlist[self.selected][1]:
				self.answer_list.append(TextInput(text='', multiline=True))

			for answer in self.qlist[self.selected][1]:
				self.answer_list.append(TextInput(text=answer, multiline=True))
		else:
			self.qstn_box.text=""
			self.answer_list = [TextInput(multiline=True), TextInput(multiline=True)]


		self.qstnLayout.add_widget(Label(text='Frage:'))
		self.qstnLayout.add_widget(self.qstn_box)
		self.qstnLayout.add_widget(Label(text='--------richtige Antwort--------'))
		self.qstnLayout.add_widget(self.answer_list[0])
		self.qstnLayout.add_widget(Label(text='--------falsche Antworten--------'))

		for box in self.answer_list[1:]:
			self.qstnLayout.add_widget(box)
		
	def move(self, right=True):
		if (right):
			if (self.selected == len(self.qlist) - 1):
				self.selected = -1
			else:
				self.selected += 1
		else:
			if (self.selected == -1):
				self.selected = len(self.qlist) - 1
			else:
				self.selected -= 1
		self.show_selected()

	def add_answer(self):
		self.answer_list.append(TextInput(multiline=True))
		self.qstnLayout.add_widget(self.answer_list[-1])

	def save(self):
		if (self.selected == -1):
			self.selected = len(self.qlist)
			self.qlist.append((self.qstn_box.text, [box.text for box in self.answer_list if box.text != '']))
		else:
			self.qlist[self.selected] = (self.qstn_box.text, [box.text for box in self.answer_list if box.text != ''])

	def back(self):
		save_questions(self.name, self.qlist)
		
		sm.switch_to(MenuScreen())

class EditQuizScreen(Screen):
	def __init__(self, **kwargs):
		super(EditQuizScreen, self).__init__(**kwargs)

		self.add_widget(QuizChooserWidget(lambda name: sm.switch_to(EditorScreen(name))))

class NewQuizScreen(Screen):
	def __init__(self, **kwargs):
		super(NewQuizScreen, self).__init__(**kwargs)

		layout = BoxLayout(orientation='vertical')
		layout.add_widget(Label(text="Wähle einen Namen für dein neues Quiz:"))
		name = TextInput(multiline=False)
		layout.add_widget(name)

		def next(inst):
			for names in listdir(datapath):
				if (names == name.text + '.quiz'):
					name.text = 'A quiz with that name already exists!'
					return

			f = open(datapath + name.text + '.quiz', 'a')
			f.close()
			sm.switch_to(EditorScreen(name.text))

		layout.add_widget(Button(text="Weiter", on_press=next))
		self.add_widget(layout)

class MenuScreen(Screen):
	def __init__(self, **kwargs):

		super(MenuScreen, self).__init__(**kwargs)

		layout = BoxLayout(orientation="vertical")

		quizzButton = Button(text="Starte Quiz", on_press=lambda inst: sm.switch_to(StartQuizScreen()))
		editButton = Button(text="Bearbeite Quiz", on_press=lambda inst: sm.switch_to(EditQuizScreen()))
		createButton = Button(text="Neues Quiz", on_press=lambda inst: sm.switch_to(NewQuizScreen()))

		layout.add_widget(quizzButton)
		layout.add_widget(editButton)
		layout.add_widget(createButton)

		self.add_widget(layout)

class QuizApp(App):

	def build(self):
		sm.switch_to(MenuScreen())
		return sm

if __name__ == '__main__':
	QuizApp().run()
