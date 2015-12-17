tool_dir = 'tools'
import sys
sys.path.append(tool_dir)
sys.path.append(tool_dir + '/inflection-0.3.1')
from variativity import *
from utilities import *
import en
import inflection
import random

def synonym_verb_conjugator(parsed_tokens, verb_token, verbs_to_conjugate, dative_object_phrase):
	
	verb_tag = verb_token.tag_
	
	nodebox_negate = False
	nodebox_participle = False
	nodebox_gerund = False
	nodebox_simple_present_third_person = False
	nodebox_simple_present_other_person = False
	nodebox_simple_past = False
	
	list_of_auxiliary_verbs = []
	for token in parsed_tokens:
		if token.head is verb_token and token.dep_ in ['aux', 'neg']:
			list_of_auxiliary_verbs.append(token.orth_.lower())
	
	#third person singular form, present tense
	if verb_tag == u'VBZ':
		set_third_person = True
		set_present_tense = True
		nodebox_simple_present_third_person = True
	#present tense, plural subject
	elif verb_tag == u'VBP':
		set_present_tense = True
		nodebox_simple_present_other_person = True
	#gerund
	elif verb_tag == u'VBG':
		nodebox_gerund = True
		set_progressive = True
		#gerund without auxiliary
		if not list_of_auxiliary_verbs:
			set_gerund_only = True
	#participle. 'having' + participle is handled separately from the regular perfect tenses
	elif verb_tag == u'VBN' and (set(['has', '\'s', 'have', '\'d', 'had', '\'d', 'having']) & set(list_of_auxiliary_verbs)):
		nodebox_participle = True
		if 'having' in list_of_auxiliary_verbs:
			set_having_participle = True
		else:
			set_perfect = True
	#a simple past tense (VBD) is commonly mistagged as a perfect (VBN)
	elif verb_tag == u'VBD' or verb_tag == u'VBN':
		nodebox_simple_past = True

	conjugated_synonyms = []
	
	for synonym_verb in verbs_to_conjugate:
		
		conjugated_synonym = synonym_verb.split(' ')[0]
		
		if nodebox_participle:
			conjugated_synonym = en.verb.past_participle(conjugated_synonym)
		
		if nodebox_gerund:
			conjugated_synonym = en.verb.present_participle(conjugated_synonym)
		
		if nodebox_simple_present_third_person:
			conjugated_synonym = en.verb.present(conjugated_synonym, person=3, negate=False)
			
		if nodebox_simple_present_other_person:
			conjugated_synonym = en.verb.present(conjugated_synonym, person=1, negate=False)
				
		if nodebox_simple_past:
			conjugated_synonym = en.verb.past(conjugated_synonym, person=1, negate=False)
		
		if dative_object_phrase:
			conjugated_synonyms.append((conjugated_synonym + ' ' + dative_object_phrase + ' ' + ' '.join(synonym_verb.split(' ')[1:])).strip())
		else:
			conjugated_synonyms.append((conjugated_synonym + ' ' + ' '.join(synonym_verb.split(' ')[1:])).strip())
	
	return '/'.join(conjugated_synonyms)

def synonym_verb_for_given_verb(parsed_tokens, verb_token, verb_index, object_index):
	
	verb_lemma = verb_token.lemma_.lower()
	
	dative_object_phrase = get_dative_object_string(parsed_tokens, verb_index, object_index, verb_token)

	if verb_lemma == 'make':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['do','create'], dative_object_phrase)
	if verb_lemma == 'take':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['receive'], dative_object_phrase)
	if verb_lemma == 'give':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['cause to have', 'provide'], dative_object_phrase)
	if verb_lemma == 'have':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['possess'], dative_object_phrase)
	if verb_lemma == 'hold':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['keep'], dative_object_phrase)
	if verb_lemma == 'do':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['perform'], dative_object_phrase)
	if verb_lemma == 'commit':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['perform'], dative_object_phrase)
	if verb_lemma == 'pay':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['give'], dative_object_phrase)
	if verb_lemma == 'provide':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['give'], dative_object_phrase)
	if verb_lemma == 'offer':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['give'], dative_object_phrase)
	if verb_lemma == 'draw':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['make'], dative_object_phrase)
	if verb_lemma == 'show':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['demonstrate'], dative_object_phrase)
	if verb_lemma == 'reach':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['arrive at'], dative_object_phrase)
	if verb_lemma == 'get':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['receive'], dative_object_phrase)
	if verb_lemma == 'lay':
		return synonym_verb_conjugator(parsed_tokens, verb_token, ['put'], dative_object_phrase)

def generate_synonym_verb_sentence(parsed_tokens, verb_token, verb_index, object_index):
	final_sentence = ''
	for token in parsed_tokens:
		if token is verb_token:
			final_sentence += '< ' + synonym_verb_for_given_verb(parsed_tokens, verb_token, verb_index, object_index) + ' > '
		else:
			final_sentence += token.orth_ + ' '
	return final_sentence.strip()

def negation_already_present(parsed_tokens, verb_token, object_token, verb_index, object_index):
	negation_list = [token for token in parsed_tokens if (token.head is object_token or (token.head is object_token and get_index_in_list(parsed_tokens, token.head) in range(verb_index, object_index))) and token.dep_ == 'det' and token.orth_.lower() == 'no' and get_index_in_list(parsed_tokens, token) in range(verb_index, object_index)]
	if negation_list:
		return True
	else:
		return False

def lvc_without_negation(parsed_tokens, verb_token, object_token, verb_index, object_index):
	negation_list = [token for token in parsed_tokens if (token.head is object_token or (token.head is object_token and get_index_in_list(parsed_tokens, token.head) in range(verb_index, object_index))) and token.dep_ == 'det' and token.orth_.lower() == 'no' and get_index_in_list(parsed_tokens, token) in range(verb_index, object_index)]
	if negation_list:
		negation_token = negation_list[0]
		lvc_wo_negation = ''
		for index in range(verb_index, object_index):
			token = parsed_tokens[index]
			if not (token is negation_token):
				lvc_wo_negation += token.orth_ + ' '
		return lvc_wo_negation
	else:
		return ''


def definite_article_already_present(parsed_tokens, verb_token, object_token, verb_index, object_index):
	definite_article_list = [token for token in parsed_tokens if (token.head is object_token or (token.head is object_token and get_index_in_list(parsed_tokens, token.head) in range(verb_index, object_index))) and token.dep_ == 'det' and token.orth_.lower() == 'the' and get_index_in_list(parsed_tokens, token) in range(verb_index, object_index)]
	if definite_article_list:
		return True
	else:
		return False

def lvc_without_definite_article(parsed_tokens, verb_token, object_token, verb_index, object_index):
	definite_article_list = [token for token in parsed_tokens if (token.head is object_token or (token.head is object_token and get_index_in_list(parsed_tokens, token.head) in range(verb_index, object_index))) and token.dep_ == 'det' and token.orth_.lower() == 'the' and get_index_in_list(parsed_tokens, token) in range(verb_index, object_index)]
	if definite_article_list:
		definite_article_token = definite_article_list[0]
		lvc_wo_definite_article = ''
		for index in range(verb_index, object_index):
			token = parsed_tokens[index]
			if not (token is definite_article_token):
				lvc_wo_definite_article += token.orth_ + ' '
		return lvc_wo_definite_article
	else:
		return ''

def object_already_pluralized(object_token):
	if inflection.pluralize(object_token.orth_.lower()) == object_token.orth_.lower():
		return True
	else:
		return False

def replace_object_with_pluralized_form(parsed_tokens, verb_token, object_token):
	sentence_with_object_pluralized = ''
	for token in parsed_tokens:
		if token is object_token:
			sentence_with_object_pluralized += inflection.pluralize(object_token.orth_) + ' > '
		elif token is verb_token:
			sentence_with_object_pluralized += '< ' + verb_token.orth_ + ' '
		elif not(token.head is object_token and ((token.dep_ == 'det' and token.orth_.lower() in ['a','an']) or (token.dep_ == 'nummod' and token.orth_.lower() in ['1','one']) or (token.dep_ == 'amod' and token.orth_.lower() in ['single','lone']))):
			sentence_with_object_pluralized += token.orth_ + ' '
	return sentence_with_object_pluralized.strip()
	
def replace_object_with_pluralized_form_phrase(parsed_tokens, verb_token, object_token, verb_index, object_index):
	lvc_with_pluralized_object = ''
		
	for index in range(verb_index, object_index):
		token = parsed_tokens[index]
		if not(token.head is object_token and ((token.dep_ == 'det' and token.orth_.lower() in ['a','an']) or (token.dep_ == 'nummod' and token.orth_.lower() in ['1','one']) or (token.dep_ == 'amod' and token.orth_.lower() in ['single','lone']))):
			lvc_with_pluralized_object += token.orth_ + ' '
	
	lvc_with_pluralized_object += inflection.pluralize(object_token.orth_)
		
	return lvc_with_pluralized_object.strip()
	
	
def replace_object_with_singularized_form_phrase(parsed_tokens, verb_token, object_token, verb_index, object_index):
	lvc_with_singularized_object = ''
		
	for index in range(verb_index, object_index):
		token = parsed_tokens[index]
		lvc_with_singularized_object += token.orth_ + ' '
	
	lvc_with_singularized_object += inflection.singularize(object_token.orth_)
		
	return lvc_with_singularized_object.strip()

def replace_verb_with_blank(parsed_tokens, verb_token, object_token):
	sentence_with_verb_removed = ''
	for token in parsed_tokens:
		if token is object_token:
			sentence_with_verb_removed += object_token.orth_ + ' > '
		elif token is verb_token:
			sentence_with_verb_removed += '< ________ '
		else:
			sentence_with_verb_removed += token.orth_ + ' '
	return sentence_with_verb_removed.strip()
	
def replace_verb_with_blank_list(parsed_tokens, verb_token, object_token, verb_index, object_index):
	sent_before_lvc = ''
	lvc_without_verb = '______ '
	sent_after_lvc = ''
	
	for index in range(verb_index):
		sent_before_lvc += parsed_tokens[index].orth_ + ' '
		
	for index in range(verb_index + 1, object_index + 1):
		lvc_without_verb += parsed_tokens[index].orth_ + ' '
		
	for index in range(object_index + 1, len(parsed_tokens)):
		sent_after_lvc += parsed_tokens[index].orth_ + ' '
		
	return [sent_before_lvc.strip(), lvc_without_verb.strip(), sent_after_lvc.strip()]
	

def passivized_phrase(parsed_tokens, verb_token, object_token, noun_phrase, verb_phrase):
	#if negated
	if [token for token in parsed_tokens if token.head is object_token and ((token.dep_ == 'nummod' and token.orth_.lower() in ['0', 'zero']) or (token.dep_ == 'det' and token.orth_.lower() == 'no'))]:
		return 'No ' + noun_phrase + ' was/were ' + en.verb.past_participle(verb_token.lemma_.lower())
	
	#if determiner
	list_of_determiners = [token for token in parsed_tokens if token.head is object_token and token.dep_ == 'det']

	if list_of_determiners:
		return list_of_determiners[0].orth_.title() + ' ' + noun_phrase + ' was/were ' + en.verb.past_participle(verb_token.lemma_.lower())
	else:
		noun_with_article = en.noun.article(noun_phrase)
		article = ''
		if noun_with_article[1] == 'n':
			article = 'An'
		else:
			article = 'A'
		return article + '/The ' + noun_phrase + ' was/were ' + en.verb.past_participle(verb_token.lemma_.lower())

def generate_other_possessive(self_possessive):
	if self_possessive in ['her', 'him', 'him/her']:
		return random.choice(['my', 'your', 'their'])
	if self_possessive == 'your':
		return random.choice(['my', 'his', 'her', 'their'])
