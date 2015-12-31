tool_dir = 'tools'

import spacy.en
import sys
from nltk.corpus import wordnet as wn	
import importlib
#setting default encoding to utf-8
importlib.reload(sys)
#sys.setdefaultencoding('utf-8')
sys.path.append(tool_dir + '/inflection-0.3.1')
sys.path.append(tool_dir)
import inflection
#import en
import nodebox_verb
import ner
from utilities import get_index_in_list

#globals for the most common unambiguous pronouns
possessive_dictionary = {'he' : 'his', 'i' : 'my', 'it' : 'its', 'she' : 'her', 'you' : 'your', 'we' : 'our', 'article' : 'its', 'this' : 'its', 'these' : 'their', 'those' : 'their', 'he\'s' : 'his', 'she\'s' : 'her', 'it\'s' : 'its', 'they' : 'their', '\'s' : 'our', 'anybody' : 'his/her', 'anyone' : 'his/her', 'somebody' : 'his/her', 'someone' : 'his/her', 'my' : 'my', 'son' : 'his', 'daughter' : 'her', 'them' : 'their', 'both' : 'their', 'all' : 'their', 'him':'his', 'himself':'his', 'her':'her', 'herself':'her', 'them':'their', 'man' : 'his', 'lady' : 'her', 'woman' : 'her', 'one':'his/her', 'us' : 'our', 'your' : 'your', 'yourself' : 'your', 'everyone' : 'their', 'everybody' : 'their', 'anything' : 'its'}
person_dictionary = {'he' : 3, 'him' : 3, 'himself' : 3, 'her' : 3, 'herself' : 3, 'everyone' : 3, 'everybody' : 3, 'anybody' : 3, 'anyone' : 3, 'somebody' : 3, 'someone' : 3, 'one' : 3, 'us' : 1, 'my' : 1, 'son' : 3, 'daughter' : 3, 'them' : 3, 'both' : 3, 'each' : 3, 'all' : 3, 'man' : 3, 'lady' : 3, 'woman' : 3, 'i' : 1, 'it' : 3, 'she' : 3, 'you' : 2, 'we' : 1, 'article' : 3, 'this' : 3, 'these' : 3, 'those' : 3, 'he\'s' : 3, 'she\'s' : 3, 'it\'s' : 3, 'they' : 3, '\'s' : 1, 'your' : 2, 'yourself' : 2, 'anything' : 3}
number_dictionary = {'he' : 1, 'him' : 1, 'himself' : 1, 'her' : 1, 'herself' : 1, 'everyone' : 2, 'everybody' : 2, 'anybody' : 1, 'anyone' : 1, 'somebody' : 1, 'someone' : 1, 'one' : 1, 'us' : 2, 'my' : 1, 'son' : 1, 'daughter' : 1, 'them' : 2, 'both' : 2, 'each' : 1, 'all' : 2, 'man' : 1, 'lady' : 1, 'woman' : 1, 'i' : 1, 'it' : 1, 'she' : 1, 'you' : 2, 'we' : 2, 'article' : 1, 'this' : 1, 'these' : 2, 'those' : 2, 'he\'s' : 1, 'she\'s' : 1, 'it\'s' : 1, 'they' : 2, '\'s' : 2, 'your' : 2, 'yourself' : 2, 'anything' : 1}

possessive_dictionary_singular = {'who' : 'his/her', 'which' : 'its', 'what' : 'its', 'whom' : 'his/her'}

set_male_names = set()
set_female_names = set()

with open('unambiguous_names', 'r') as names_file:
	content = names_file.readlines()
	for name in content[0].split(','):
		set_male_names.add(name)
	for name in content[1].split(','):
		set_female_names.add(name)

def possessive_referencing_subject_already_present(parsed_tokens, verb_token, object_token, verb_index, object_index, possessive_string):
	list_of_possessives = [token for token in parsed_tokens if (token.head is object_token or (get_index_in_list(parsed_tokens, token.head) in range(verb_index, object_index) and token.head is object_token)) and token.dep_ == 'poss' and token.orth_ in possessive_string and get_index_in_list(parsed_tokens, token) in range(verb_index, object_index)]
	
	if list_of_possessives:
		return True
	else:
		return False

def verb_phrase_for_possessive_replacement(parsed_tokens, verb_token, object_token, verb_phrase, subject_person, subject_number):
	
	list_of_negative_modifiers = [token for token in parsed_tokens if token.head is object_token and ((token.dep_ == 'nummod' and token.orth_.lower() in ['0', 'zero']) or (token.dep_ == 'det' and token.orth_.lower() == 'no'))]
	
	if not list_of_negative_modifiers:
		return verb_phrase
	
	verb_lemma = verb_token.lemma_.lower()
	verb_tag = verb_token.tag_
	
	nodebox_negate = False
	nodebox_participle = False
	nodebox_gerund = False
	nodebox_simple_present_third_person = False
	nodebox_simple_present_other_person = False
	nodebox_simple_past = False
	
	aux_verb_buffer = []
	for token in parsed_tokens:
		if token.head is verb_token and token.dep_ in ['aux', 'neg']:
			aux_verb_buffer.append(token.orth_.lower())
	
	#third person singular form, present tense
	if verb_tag == u'VBZ':
		nodebox_simple_present_third_person = True
	#present tense, plural subject
	elif verb_tag == u'VBP':
		nodebox_simple_present_other_person = True
	#gerund
	elif verb_tag == u'VBG':
		nodebox_gerund = True
	#participle. 'having' + participle is handled separately from the regular perfect tenses
	elif verb_tag == u'VBN' and (set(['has', '\'s', 'have', '\'d', 'had', '\'d', 'having']) & set(aux_verb_buffer)):
		nodebox_participle = True
	#a simple past tense (VBD) is commonly mistagged as a perfect (VBN)
	elif verb_tag == u'VBD' or verb_tag == u'VBN':
		nodebox_simple_past = True
	
	if nodebox_participle:
		if aux_verb_buffer:
			aux_verb_buffer.insert(1, 'not')
			if get_index_in_list(parsed_tokens, verb_token) > 0 and parsed_tokens[get_index_in_list(parsed_tokens, verb_token)].orth_.lower() == aux_verb_buffer[0]:
				aux_verb_buffer = aux_verb_buffer[1:]
			return ' '.join(aux_verb_buffer) + ' ' + nodebox_verb.past_participle(verb_lemma)
		else:
			return 'not ' + nodebox_verb.past_participle(verb_lemma)
	
	if nodebox_gerund:
		if aux_verb_buffer:
			aux_verb_buffer.insert(1, u'not')
			if get_index_in_list(parsed_tokens, verb_token) > 0 and parsed_tokens[get_index_in_list(parsed_tokens, verb_token)].orth_.lower() == aux_verb_buffer[0]:
				aux_verb_buffer = aux_verb_buffer[1:]
			return ' '.join(aux_verb_buffer) + ' ' + nodebox_verb.present_participle(verb_lemma)
		else:
			return 'not ' + nodebox_verb.present_participle(verb_lemma)

	if nodebox_simple_present_third_person:
		return 'does not ' + nodebox_verb.present(verb_lemma, person=2, negate=False)	
		
	if nodebox_simple_present_other_person:
		return 'do not ' + nodebox_verb.present(verb_lemma, person=1, negate=False)
			
	if nodebox_simple_past:
		return 'did not ' + nodebox_verb.present(verb_lemma, person=2, negate=False)
	
	if aux_verb_buffer:
		aux_verb_buffer.insert(1, u'not')
		if get_index_in_list(parsed_tokens, verb_token) > 0 and parsed_tokens[get_index_in_list(parsed_tokens, verb_token)].orth_.lower() == aux_verb_buffer[0]:
			aux_verb_buffer = aux_verb_buffer[1:]
		return ' '.join(aux_verb_buffer) + ' ' + verb_lemma
	else:
		if str(subject_person) == '3' and str(subject_number) == '1':
			return 'does not ' + verb_lemma
		else:
			return 'do not ' + verb_lemma


def person_or_not (sentence, subject_word, ner_tagger, parsed_tokens, verb_token, subj_token, verb_phrase):
	#perform NER
	entities = ner_tagger.get_entities(sentence)
	
	#if a PERSON named entity is found, assume singular, and attach 'his/her'
	if 'PERSON' in entities and [person_name for person_name in entities['PERSON'] if subject_word in person_name.lower()]:
		if subject_word in set_male_names:
			return [3, 1, u'his', verb_phrase]
		elif subject_word in set_female_names:
			return [3, 1, u'her', verb_phrase]
		else:
			return [3, 1, u'his/her', verb_phrase]
		
	#if a LOCATION or ORGANIZATION named entity is found, assume singular, and attach 'its'
	if 'ORGANIZATION' in entities and [person_name for person_name in entities['ORGANIZATION'] if subject_word in person_name.lower()]:
		return [3, 1, u'its', verb_phrase]
	if 'LOCATION' in entities and [person_name for person_name in entities['LOCATION'] if subject_word in person_name.lower()]:
		return [3, 1, u'its', verb_phrase]
	#check for pronoun
	if subject_word in possessive_dictionary:
		return [person_dictionary[subject_word], number_dictionary[subject_word], possessive_dictionary[subject_word], verb_phrase]
	if subject_word in possessive_dictionary_singular:
		return [3, 1, possessive_dictionary_singular[subject_word], verb_phrase]
	#check whether 'person' is a hypernym
	if wn.synsets(subj_token.lemma_.lower(), pos=wn.NOUN):
		subj_synset = wn.synset(subj_token.lemma_.lower() + '.n.01')
		if subj_synset == wn.synset('person.n.01') or subj_synset is wn.synset('person.n.01') or wn.synset('person.n.01') in list(subj_synset.closure(lambda s: s.hypernyms())):
			return [3, 1, u'his/her', verb_phrase]
		else:
			return [3, 1, u'its', verb_phrase]
	sys.stderr.write('Can\'t determine person or not\n')
	return None

def comp_closure(parsed_tokens, verb_token):
	list_of_comps = [verb_token]
	while True:
		current_comp = list_of_comps[-1]
		list_of_subjects = [subj_token for subj_token in parsed_tokens if subj_token.dep_ in ["nsubj", "nsubjpass"] and subj_token.head is current_comp]
		list_of_subjects.extend([subj_token for subj_token in parsed_tokens if current_comp.dep_ in ["acl"] and current_comp.head is subj_token])
		if list_of_subjects:
			if list_of_subjects[0].lemma_.lower() in ["that", "who", "which"]:
				new_list = [subj_token for subj_token in parsed_tokens if current_comp.dep_ in ["relcl"] and current_comp.head is subj_token]
				if new_list:
					return new_list[0], list_of_comps
				else:
					return list_of_subjects[0], list_of_comps
			else:
				return list_of_subjects[0], list_of_comps

		
		new_comp_list = [new_comp for new_comp in parsed_tokens if current_comp.dep_ in ["acomp", "xcomp", "advcl", "ccomp", "conj"] and current_comp.head is new_comp]
		new_comp_list.extend([new_comp for new_comp in parsed_tokens if current_comp.dep_ == "pcomp" and current_comp.head.dep_ == "prep" and current_comp.head.head is new_comp])

		if new_comp_list:
			list_of_comps.append(new_comp_list[0])

		else:
			return None, list_of_comps


def get_subject(parsed_tokens, verb_token):
	# Direct subject

	#list_of_subjects_list = [subj_token for subj_token in parsed_tokens if subj_token.dep_ in ["nsubjpass", "nsubj", "acl"] and subj_token.head is verb_token]
	#compounded_components = None
	#if list_of_subjects_list:
	#	return list_of_subjects_list[0], compounded_components

	# Comp closure	
	list_of_subjects, compounded_components = comp_closure(parsed_tokens, verb_token)
	if not list_of_subjects:
		#Aux closure
		if "aux" in verb_token.dep_:
			list_of_subjects, compounded_components = comp_closure(parsed_tokens, verb_token.head)
		elif verb_token.dep_ == "pcomp":
			list_of_subjects_list = [tok for tok in parsed_tokens if verb_token.head.head is tok and verb_token.head.dep_ == 'prep']
			if list_of_subjects_list:
				list_of_subjects = list_of_subjects_list[0]
		elif verb_token.dep_ == "xcomp":
			list_of_subjects_list = [tok for tok in parsed_tokens if verb_token.head is tok.head and tok.dep_ == 'dobj']
			if list_of_subjects_list:
				list_of_subjects = list_of_subjects_list[0]
		#return list_of_subjects, compounded_components

	return list_of_subjects, compounded_components


def get_subject_properties(parsed_tokens, verb_token, object_token, ner_tagger, sentence, verb_phrase):
	"""
	sys.stderr.write('\n\nWriting parse\n\n\n-------------------\n\n')
	for t in parsed_tokens:
		sys.stderr.write(t.orth_ + ' ' + t.dep_ + ' ' + t.head.orth_ + ' ' + t.tag_ + '\n')
	sys.stderr.write('-------------------\n\n\n')
	"""
	subject, comps = get_subject(parsed_tokens, verb_token)

	if subject:
		subj_token = subject
		subject_word = subj_token.orth_.lower()
		sys.stderr.write('LVC phrase start and end points \n' + verb_token.orth_ + ' ' + object_token.orth_ + '\nSubject word is \n' + subject_word + '\nfor sentence \n' + sentence + '\n\n')
		
		#if the verb conjugation is singular 3rd person for sure
		if (verb_token.tag_ == u'VBZ') or ((verb_token.tag_ == u'VBG' or verb_token.tag_ == u'VBN') and [aux_verb_token for aux_verb_token in parsed_tokens if aux_verb_token.dep_ == u'aux' and aux_verb_token.head is verb_token and aux_verb_token.tag_ == u'VBZ']):
			return person_or_not (sentence, subject_word, ner_tagger, parsed_tokens, verb_token, subj_token, verb_phrase_for_possessive_replacement(parsed_tokens, verb_token, object_token, verb_phrase, 3, 1))
		
		#check if it's in the tiny pronoun dictionary
		if subject_word in possessive_dictionary:
			return [person_dictionary[subject_word], number_dictionary[subject_word], possessive_dictionary[subject_word], verb_phrase_for_possessive_replacement(parsed_tokens, verb_token, object_token, verb_phrase, person_dictionary[subject_word], number_dictionary[subject_word])]
		
		#if the subject is not 'i' or 'you' or 'we' and the verb form is not 3rd person singular
		if (verb_token.tag_ == u'VBP') or ((verb_token.tag_ == u'VBG' or verb_token.tag_ == u'VBN') and [aux_verb_token for aux_verb_token in parsed_tokens if aux_verb_token.dep_ == u'aux' and aux_verb_token.head is verb_token and aux_verb_token.tag_ == u'VBP']):
			return [3, 2, u'their', verb_phrase_for_possessive_replacement(parsed_tokens, verb_token, object_token, verb_phrase, 3, 2)]
		
		#if the subject has a conjunction	
		compounded_subjects = [tok.orth_.lower() for tok in parsed_tokens if tok.dep_ == "conj" and tok.head is subj_token]
		if compounded_subjects:
			if [tok for tok in parsed_tokens if tok.orth_.lower() == "and" and tok.dep_ == "cc" and tok.head is subj_token]:
				if u'i' in compounded_subjects:
					return [1, 2, u'our', verb_phrase]
				elif 'you' in compounded_subjects:
					return [2, 2, u'your', verb_phrase]
				else:
					return [3, 2, u'their', verb_phrase]
		
		#if the subject is plural according to the inflector, and the verb form is not singular - doing this test only for dictionary words and not for NEs which were not detected
		if wn.synsets(subj_token.lemma_.lower(), pos=wn.NOUN) and inflection.pluralize(subject_word) == subject_word and inflection.singularize(subject_word) != subject_word:
			return [3, 2, u'their', verb_phrase_for_possessive_replacement(parsed_tokens, verb_token, object_token, verb_phrase, 3, 2)]
		
		entities = ner_tagger.get_entities(sentence)
	
		#if a PERSON named entity is found, assume singular, and attach 'his/her'
		if 'PERSON' in entities and [person_name for person_name in entities['PERSON'] if subject_word in person_name.lower()]:
			if subject_word in set_male_names:
				return [3, 1, u'his', verb_phrase]
			elif subject_word in set_female_names:
				return [3, 1, u'her', verb_phrase]
			else:
				return [3, 1, u'his/her', verb_phrase]
		#if a LOCATION or ORGANIZATION named entity is found, assume singular, and attach 'its'
		if 'ORGANIZATION' in entities and [person_name for person_name in entities['ORGANIZATION'] if subject_word in person_name.lower()]:
			return [3, 1, u'its', verb_phrase]
		if 'LOCATION' in entities and [person_name for person_name in entities['LOCATION'] if subject_word in person_name.lower()]:
			return [3, 1, u'its', verb_phrase]


		# Riskiest of them all - singular noun
		if wn.synsets(subj_token.lemma_.lower(), pos=wn.NOUN) and inflection.pluralize(subject_word) != subject_word and inflection.singularize(subject_word) == subject_word:
			return person_or_not (sentence, subject_word, ner_tagger, parsed_tokens, verb_token, subj_token, verb_phrase_for_possessive_replacement(parsed_tokens, verb_token, object_token, verb_phrase, 3, 1))
			
		else:
			sys.stderr.write('Failed to determine subject properties\n\n\n')
			return None
				
		
	else:
		sys.stderr.write('Too many subjects ' + '\n\n\n')
		return None
