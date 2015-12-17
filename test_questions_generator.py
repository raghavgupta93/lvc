tool_dir = 'tools'

import spacy.en
from spacy.en.attrs import IS_ALPHA, IS_UPPER, IS_PUNCT, LIKE_URL, LIKE_NUM
import gzip
import sys
import xlsxwriter
import os
from nltk.corpus import wordnet as wn
sys.path.append(tool_dir + '/inflection-0.3.1')
sys.path.append(tool_dir)
import inflection
import ner
import en
from nltk.corpus import wordnet as wn
from difflib import get_close_matches as gcm
import urllib
import urllib2
import json
from variativity import *
from utilities import *
from possessive_self import *
from other_features import *

#setting default encoding to utf-8
reload(sys)
sys.setdefaultencoding('utf-8')

def preprocess_verb_conjugator_lexicon(conjugated_verbs):
	conjugated_verbs_file = open(tool_dir + '/en/verb/verb.txt', 'r')
	for line in conjugated_verbs_file:
		conjugated_verbs.add(line.split(',')[0])

def word_exists_in_wiktionary(word):
	url = 'https://en.wiktionary.org/w/api.php?action=query&titles=' + word + '&format=json'
	if 'missing' in json.load(urllib.urlopen(url)):
		return False
	else:
		return True

#compare the frequencies of the given lemma as a verb versus as a noun in the BNC. Returns true if the noun occurrence is not more than 4 times as frequent as the verb occurrence
def compare_lemma_verb_noun_frequencies(lemma, catvar_noun_dict, bnc_noun_frequencies, bnc_verb_frequencies):
	noun_frequency = 0.
	verb_frequency = 0.
	if lemma in bnc_noun_frequencies:
		noun_frequency = bnc_noun_frequencies[lemma]
	
	list_of_verbs = list(catvar_noun_dict[lemma])
	for verb in list_of_verbs:
		if verb in bnc_verb_frequencies:
			verb_frequency += bnc_verb_frequencies[verb]

	if noun_frequency != 0 and noun_frequency <= 2 * verb_frequency:
		return True
	else:
		return False

#loading the BNC noun and verb frequencies (for lemma) in two dictionaries
def load_bnc_frequencies(bnc_noun_frequencies, bnc_noun_frequencies_file, bnc_verb_frequencies, bnc_verb_frequencies_file):
	for line in bnc_noun_frequencies_file:
		toks = line.split()
		if len(toks) == 2:
			bnc_noun_frequencies[toks[0]] = int(toks[1])
			
	for line in bnc_verb_frequencies_file:
		toks = line.split()
		if len(toks) == 2:
			bnc_verb_frequencies[toks[0]] = int(toks[1])

#check if there is a catvar cluster containing the given noun lemma that also contains a verb
def noun_to_verb_in_catvar(catvar_file, lemma, catvar_noun_dict, catvar_no_verb_set):
	if lemma in catvar_no_verb_set:
		return False
	if lemma in catvar_noun_dict:
		return True
	
	catvar_file.seek(0, 0)
	string_to_search = lemma + u'_N%'
	verb_marker = u'_V%'
	at_least_one_match = False
	list_of_verbs = []
	for line in catvar_file:
		if line.find(string_to_search) == 0 or u'#' + string_to_search in line:
			if verb_marker in line:
				cluster_entries = line.split(u'#')
				for entry in cluster_entries:
					if verb_marker in entry:
						at_least_one_match = True
						list_of_verbs.append(entry.split(u'_')[0])
	
	if at_least_one_match:
		catvar_noun_dict[lemma] = list()
		for verb in list_of_verbs:
			catvar_noun_dict[lemma].append(verb)
	else:
		catvar_no_verb_set.add(lemma)
						
	return at_least_one_match

#this is a dictionary for fast lookup of catvar entries
catvar_noun_dict = dict()

#and this a set of entries with no verb, for quick lookup
catvar_no_verb_set = set()

#a list of the verbs we can conjugate
conjugated_verbs = set()

#nlp pipeline (tagger and parser)
nlp_pipeline = spacy.en.English()

#enlist the verbs we can conjugate. everything else, well, sorry
preprocess_verb_conjugator_lexicon(conjugated_verbs)

#verb - prep pairs within 3 tokens- output file
verb_prep_file = open('verb_prep_combinations', 'w')
verb_prep_file_noun_attach = open('verb_prep_combinations_noun_attachment', 'w')

#list of allowed verbs
allowed_verbs = ['make', 'take', 'give', 'have', 'hold', 'do', 'commit', 'pay', 'provide', 'offer', 'draw', 'show', 'reach', 'get', 'lay']

#exhaustive adjective to adverb mapping
adjective_adverb_dict = dict()

#and a list of adjectives I can't find an adverb for
no_adverb_set = set()

#open catvar file
catvar_file = open(tool_dir + "/catvar/catvar21.signed", "r")

#mapping of LVC object to preposition, if exists
object_preposition_dict = dict()

#set of LVC objects that do not strongly prefer a particular preposition
no_preposition_objects = set()

#counter
variativity_counter = 0
possessive_self_counter = 0
possessive_other_counter = 0
negation_counter = 0
definite_article_counter = 0
omission_counter = 0
pluralization_counter = 0


#workbooks
workbook_variativity = xlsxwriter.Workbook('variativity_second_half.xlsx')
worksheet_variativity = workbook_variativity.add_worksheet()
workbook_possessive_self = xlsxwriter.Workbook('possessive_self_second_half.xlsx')
worksheet_possessive_self = workbook_possessive_self.add_worksheet()
workbook_possessive_other = xlsxwriter.Workbook('possessive_other_second_half.xlsx')
worksheet_possessive_other = workbook_possessive_other.add_worksheet()
workbook_negation = xlsxwriter.Workbook('negation_second_half.xlsx')
worksheet_negation = workbook_negation.add_worksheet()
workbook_definite_article = xlsxwriter.Workbook('definite_article_second_half.xlsx')
worksheet_definite_article = workbook_definite_article.add_worksheet()
workbook_omission = xlsxwriter.Workbook('omission_second_half.xlsx')
worksheet_omission = workbook_omission.add_worksheet()
workbook_pluralization = xlsxwriter.Workbook('pluralization_second_half.xlsx')
worksheet_pluralization = workbook_pluralization.add_worksheet()

#ner tagger
ner_tagger = ner.SocketNER(host='localhost', port=8080)

#load BNC noun and verb lemma frequencies in dictionaries
bnc_noun_frequencies = dict()
bnc_verb_frequencies = dict()
bnc_noun_frequencies_file = open(tool_dir + "/lists/bnc_noun_list", "r")
bnc_verb_frequencies_file = open(tool_dir + "/lists/bnc_verb_list", "r")
load_bnc_frequencies(bnc_noun_frequencies, bnc_noun_frequencies_file, bnc_verb_frequencies, bnc_verb_frequencies_file)
bnc_noun_frequencies_file.close()
bnc_verb_frequencies_file.close()

#open wikipedia dump
with open(sys.argv[1], 'r') as fin_file:
	#storing stuff during processing a sentence
	sentence = ""
	candidate_object_token_numbers = []
	fin = fin_file.readlines()
	
	#read corpus line by line
	for super_index in range(len(fin)):
		line = fin[super_index]
		if ' ||| ' not in line:
			continue
		components = line.split(' ||| ')
		lvc_phrase_lemmatized = unicode(components[0].strip())
		sentence = unicode(components[1].strip())
		#print fin[super_index-1], fin[super_index-1].split(), unicode(fin[super_index-1].split()), unicode(fin[super_index-1].split())[-1]
		true_label = unicode(fin[super_index-1].split()[-1])[-1]
		length_of_lvc_phrase = len(lvc_phrase_lemmatized.split())

		#parsing the sentence
		parsed_tokens = nlp_pipeline(sentence)
		
		#add all probable direct object candidates to a list
		for index in range(len(parsed_tokens) - length_of_lvc_phrase + 1):
			#probable start of lvc phrase
			if parsed_tokens[index].lemma_.lower() == lvc_phrase_lemmatized.split()[0].lower():
				#print "For sentence- " + sentence + " LVC phrase may start at index " + unicode(str(index))
				is_start_of_lvc_phrase = True
				for inner_index in range(1, length_of_lvc_phrase):
					if not (lvc_phrase_lemmatized.split()[inner_index].lower() in [parsed_tokens[index + inner_index].lemma_.lower(), parsed_tokens[index + inner_index].orth_.lower()]):
						sys.stderr.write(lvc_phrase_lemmatized.split()[inner_index].lower() + ' neither ' + parsed_tokens[index + inner_index].lemma_.lower() + ' or ' + parsed_tokens[index + inner_index].orth_.lower())
						is_start_of_lvc_phrase = False
						if not candidate_object_token_numbers:
							sys.stderr.write(sentence + '\nBehenchod\n')
						break
				if is_start_of_lvc_phrase:
					candidate_object_token_numbers.append(index + length_of_lvc_phrase - 1)
			"""#if there's a direct object, to start with 
			if (parsed_tokens[index].dep_.strip() == "dobj"):
				#if the verb belongs to the list of allowed verbs
				if parsed_tokens[index].head.lemma_ in allowed_verbs:
					#if the object's head verb is not more than 6 tokens behind the direct object
					poss_head_index = get_index_in_list(parsed_tokens, parsed_tokens[index].head)	
					if poss_head_index < index and index - poss_head_index < 7:	
						#if the object is not a punctuation mark or number-like or url-like
						if not(parsed_tokens[index].check_flag(IS_PUNCT) or parsed_tokens[index].check_flag(LIKE_URL) or parsed_tokens[index].check_flag(LIKE_NUM)):
							#if the noun has a verb in the same cluster from catvar
							if noun_to_verb_in_catvar(catvar_file, parsed_tokens[index].lemma_.lower(), catvar_noun_dict, catvar_no_verb_set):
								#check if the verb has a conjugation in our verb conjugator
								if [verb for verb in catvar_noun_dict[parsed_tokens[index].lemma_.lower()] if verb in conjugated_verbs]:		
									#check whether the nominal form of this noun appears much more frequently compared to that of the verbal form in the BNC
									if compare_lemma_verb_noun_frequencies(parsed_tokens[index].lemma_.lower(), catvar_noun_dict, bnc_noun_frequencies, bnc_verb_frequencies):
										#add this token to the list of possible light verb objects for this sentence: there may be multiple
										candidate_object_token_numbers.append(index)"""
		
		#now consider each candidate, construct verb phrase, noun phrase, lvc phrase
		for object_index in candidate_object_token_numbers:
			#some initializations
			object_token = parsed_tokens[object_index]
			object_headword = object_token.orth_
			
			verb_token = object_token.head
			verb_index = get_index_in_list(parsed_tokens, verb_token)
			verb_headword = verb_token.orth_
			if verb_token.lemma_.lower() != lvc_phrase_lemmatized.split()[0].lower():
				sys.stderr.write(sentence + '\n\n')
				continue
			
			"""list_of_subjects = [subject_token for subject_token in parsed_tokens if subject_token.dep_ == "nsubj" and subject_token.head is verb_token]
			if len(list_of_subjects) != 1:
				sys.stderr.write(sentence + '\n\n')
				continue
			
			subject_token = list_of_subjects[0]
			subject_index = get_index_in_list(parsed_tokens, subject_token)
			subject_headword = subject_token.orth_"""
			
			lvc_phrase = parsed_tokens[verb_index].orth_
			verb_phrase = parsed_tokens[verb_index].orth_
			noun_phrase = u''
			
			#create verb phrase, noun phrase, lvc phrase
			for index in range(verb_index + 1, object_index + 2):
				if index >= len(parsed_tokens):
					continue
				#to accommodate for the particle occurring beyond the noun phrase
				if (index == object_index + 1):
					if parsed_tokens[index].dep_.strip() == u'prt' and get_index_in_list(parsed_tokens, parsed_tokens[index].head) == verb_index:
						verb_phrase += u' ' + parsed_tokens[index].orth_
						lvc_phrase += u' ' + parsed_tokens[index].orth_
				#adding only compound noun modifiers to the noun phrase, discarding 'amod'
				else:
					lvc_phrase += u' ' + parsed_tokens[index].orth_
					if parsed_tokens[index].dep_.strip() == u'prt' and get_index_in_list(parsed_tokens, parsed_tokens[index].head) == verb_index:
						verb_phrase += u' ' + parsed_tokens[index].orth_
					if parsed_tokens[index].dep_.strip() == u'compound' and get_index_in_list(parsed_tokens, parsed_tokens[index].head) == object_index:
						noun_phrase += parsed_tokens[index].orth_ + u' '
			noun_phrase += parsed_tokens[object_index].orth_
			
			
			#at this point we're ready to do all the shit
			#but first, some filters!
			
			#if there's a comma or parentheses in the LVC phrase, skip
			if u',' in lvc_phrase or u'(' in lvc_phrase or u')' in lvc_phrase:
				sys.stderr.write(sentence + '\nStep4\n')
				continue
			#if the verb is preceded or the noun is followed by a hyphen, skip
			phrase_index = sentence.find(lvc_phrase)
			if phrase_index >= 2 and sentence[phrase_index - 2] == u'-':
				sys.stderr.write(sentence + '\nStep5\n')
				continue
			if phrase_index + 2 < len(sentence) and sentence[phrase_index + 2] == u'-':
				sys.stderr.write(sentence + '\nStep6\n')
				continue
			#if lvc_phrase not in tokenized sentence, leave it
			if lvc_phrase not in sentence:
				sys.stderr.write(sentence + '\nStep7\n')
				continue			
			
			#now print feature values
			string_sentences = ''
			
			stuff_to_write_to_workbooks = []
			
			#string_sentences += 'ORIGINAL SENTENCE\n' + sentence.replace(lvc_phrase, '< ' + lvc_phrase + ' >') + '\n\n'
			
			#possessive
			subject_properties = get_subject_properties(parsed_tokens, verb_token, object_token, ner_tagger, sentence, verb_phrase)
			if not subject_properties:
				sys.stderr.write(sentence + '\nStep1\n')
				continue
			elif possessive_referencing_subject_already_present(parsed_tokens, verb_token, object_token, verb_index, object_index, subject_properties[2]):
				a = 0
				#string_sentences += 'POSSESSIVE REFERENCING THE SUBJECT\nAnswer - YES\n\n'
			else:
				possessive_self_counter += 1
				replacement_phrase = ''
				dative_object_phrase = get_dative_object_string(parsed_tokens, verb_index, object_index, verb_token)
				if dative_object_phrase:
					replacement_phrase = subject_properties[3] + ' ' + dative_object_phrase + ' ' + subject_properties[2] + ' ' + noun_phrase
				else:
					replacement_phrase = subject_properties[3] + ' ' + subject_properties[2] + ' ' + noun_phrase
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, replacement_phrase, sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_possessive_self, possessive_self_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
				
				other_possessive = generate_other_possessive(subject_properties[2])
					#worksheet_possessive_self.write(possessive_self_counter, column_index, if_blank_return_space(list_of_arguments[column_index]))
				#string_sentences += 'POSSESSIVE REFERENCING THE SUBJECT\nDoes this sentence make sense?\n' + sentence.replace(lvc_phrase, '< ' + replacement_phrase + ' >') + '\n\n'
			
			#variativity
			if not noun_to_verb_in_catvar(catvar_file, object_token.lemma_.lower(), catvar_noun_dict, catvar_no_verb_set):
				sys.stderr.write(sentence + '\nStep2\n')
				sys.stderr.write(object_token.lemma_.lower() + '\n')
				continue
			list_of_related_verbs = catvar_noun_dict[object_token.lemma_.lower()]
			verb = list_of_related_verbs[0]
			if verb not in conjugated_verbs or verb != en.verb.present(verb) or not subject_properties:
				sys.stderr.write(sentence + '\nStep3\n')
				sys.stderr.write(verb + '\n')
				continue
			"""variativity_replacement_strings = variativity_replacement(sentence, verb_token, object_token, object_index, verb_index, parsed_tokens, verb, lvc_phrase, catvar_file, adjective_adverb_dict, no_adverb_set, object_preposition_dict, no_preposition_objects, subject_properties[0], subject_properties[1])
			if variativity_replacement_strings:
				new_sentence = variativity_replacement_strings[0]
				phrase_to_replace = variativity_replacement_strings[1]
				final_phrase_active = variativity_replacement_strings[2]
				final_phrase_passive = variativity_replacement_strings[3]
				#string_sentences += 'VARIATIVITY\nDoes this sentence make sense and convey a meaning similar to the original sentence?\n' + new_sentence.replace(phrase_to_replace, '< ' + final_phrase_active + '/' + final_phrase_passive + ' >') + '\n\n'
				variativity_counter += 1
				list_of_arguments = [sentence.split(phrase_to_replace)[0].strip(), phrase_to_replace, sentence.split(phrase_to_replace)[1].strip(), new_sentence.split(phrase_to_replace)[0].strip(), final_phrase_active, final_phrase_passive, new_sentence.split(phrase_to_replace)[1].strip(), true_label]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_variativity, variativity_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
					#worksheet_variativity.write(variativity_counter, column_index, if_blank_return_space(list_of_arguments[column_index]))	
				string_sentences += ' ||| '.join(list_of_arguments)
			else:
				sys.stderr.write(sentence + '\n\n')
				continue"""
			
			#synonym verb
			#string_sentences += 'SYNONYM VERB\nDoes this sentence make sense?\n' +  generate_synonym_verb_sentence(parsed_tokens, verb_token, verb_index, object_index) + '\n\n'
			
			#negation
			if negation_already_present(parsed_tokens, verb_token, object_token, verb_index, object_index):
				a = 0
				negation_counter += 1
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, lvc_without_negation(parsed_tokens, verb_token, object_token, verb_index, object_index).strip(), sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_negation, negation_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
				
				#string_sentences += 'NEGATION WITH \'NO\'\nAnswer - YES\n\n'
			else:
				dative_object_phrase = get_dative_object_string(parsed_tokens, verb_index, object_index, verb_token)
				replacement_phrase = ''
				negation_counter += 1
				if dative_object_phrase:
					replacement_phrase = verb_phrase + ' ' + dative_object_phrase + ' no ' + noun_phrase
				else:
					replacement_phrase = verb_phrase + ' no ' + noun_phrase
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, replacement_phrase, sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_negation, negation_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
					#worksheet_negation.write(negation_counter, column_index, if_blank_return_space(list_of_arguments[column_index]))	
				#string_sentences += 'NEGATION WITH \'NO\'\nDoes this sentence make sense?\n' + sentence.replace(lvc_phrase, '< ' + negated_phrase + ' >') + '\n\n'
			
			#definite article
			if definite_article_already_present(parsed_tokens, verb_token, object_token, verb_index, object_index):
				a = 0
				definite_article_counter += 1
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, lvc_without_definite_article(parsed_tokens, verb_token, object_token, verb_index, object_index).strip(), sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_definite_article, definite_article_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])	
				
				#string_sentences += 'DEFINITE ARTICLE\nAnswer - YES\n\n'
			else:
				definite_article_counter += 1
				replacement_phrase = ''
				dative_object_phrase = get_dative_object_string(parsed_tokens, verb_index, object_index, verb_token)
				if dative_object_phrase:
					replacement_phrase = verb_phrase + ' ' + dative_object_phrase + ' the ' + noun_phrase
				else:
					replacement_phrase = verb_phrase + ' the ' + noun_phrase
				
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, replacement_phrase, sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_definite_article, definite_article_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])	
				
				#string_sentences += 'DEFINITE ARTICLE\nDoes this sentence make sense?\n' + sentence.replace(lvc_phrase, '< ' + negated_phrase + ' >') + '\n\n'
			
			#pluralization
			pluralization_counter += 1
			if object_already_pluralized(object_token):
				a = 0
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, replace_object_with_singularized_form_phrase(parsed_tokens, verb_token, object_token, verb_index, object_index), sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_pluralization, pluralization_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
				
				#string_sentences += 'PLURALIZING THE LVC OBJECT\nAnswer - YES\n\n'
			else:
				a = 0
				list_of_arguments = [sentence.split(lvc_phrase)[0].strip(), lvc_phrase, replace_object_with_pluralized_form_phrase(parsed_tokens, verb_token, object_token, verb_index, object_index), sentence.split(lvc_phrase)[1].strip()]
				for column_index in range(len(list_of_arguments)):
					stuff_to_write_to_workbooks.append([worksheet_pluralization, pluralization_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
				#string_sentences += 'PLURALIZING THE LVC OBJECT\nDoes thie sentence make sense?\n' + replace_object_with_pluralized_form(parsed_tokens, verb_token, object_token) + '\n\n'
			
			#verb omission
			omission_counter += 1
			list_of_arguments = replace_verb_with_blank_list(parsed_tokens, verb_token, object_token, verb_index, object_index)
			for column_index in range(len(list_of_arguments)):
				stuff_to_write_to_workbooks.append([worksheet_omission, omission_counter, column_index, if_blank_return_space(list_of_arguments[column_index])])
			#string_sentences += 'OMITTING THE VERB\nGiven the sentence with one verb removed, can you still guess the activity taking place in the phrase in angled brackets?\n' + replace_verb_with_blank(parsed_tokens, verb_token, object_token) + '\n\n'
			
			#passivization
			#string_sentences += 'PASSIVIZATION\nDoes it make sense to say the following?\n' + passivized_phrase(parsed_tokens, verb_token, object_token, noun_phrase, verb_phrase) + '\n\n'
			
			#print string_sentences + '-------------------\n'
			#print string_sentences
			
			for item in stuff_to_write_to_workbooks:
				item[0].write(item[1], item[2], item[3])
		
		#empty all buffers and continue to the next sentence
		sentence = u''
		candidate_object_token_numbers[:] = []

catvar_file.close()
workbook_variativity.close()
workbook_possessive_self.close()
workbook_possessive_other.close()
workbook_negation.close()
workbook_definite_article.close()
workbook_omission.close()
workbook_pluralization.close()
