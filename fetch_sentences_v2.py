#https://the.sketchengine.co.uk/bonito/run.cgi/first?corpname=preloaded%2Fbnc2&reload=&iquery=take+care&queryselector=iqueryrow&lemma=&lpos=&phrase=&word=&wpos=&char=&cql=&default_attr=lc&fc_lemword_window_type=both&fc_lemword_wsize=5&fc_lemword=&fc_lemword_type=all&fc_pos_window_type=both&fc_pos_wsize=5&fc_pos_type=all&usesubcorp=&fsca_bncdoc.genre=&fsca_u.who=

import os
import time

def locations_of_substring(string, substring):

    substring_length = len(substring)    
    def recurse(locations_found, start):
        location = string.find(substring, start)
        if location != -1:
            return recurse(locations_found + [location], location+substring_length)
        else:
            return locations_found

    return recurse([], 0)




i = 0
with open('lvc_BNC_unseen.txt', 'r') as mfile:
	content = mfile.readlines()
	for index in range(len(content)):
		line = content[index]
		already_processed_file = open('/home/raghav/summer/corpora/Roth/sentences_unseen', 'r')
		already_processed_lines = already_processed_file.readlines()
		if line in already_processed_lines:
			continue
		components = line.split()
		if not (components[2][0] in ['-', '+']):
			continue
		if not (content[index+1].split()[2][0] in ['-', '+']):
			continue
		lvc_string = components[1].replace("_", " ")
		ID = components[0][5:8]
		i += 1
		query = "\"https://the.sketchengine.co.uk/bonito/run.cgi/first?corpname=preloaded%2Fbnc2&reload=&iquery=" + components[1].replace("_", "+") + "&queryselector=iqueryrow&lemma=&lpos=&phrase=&word=&wpos=&char=&cql=&default_attr=lc&fc_lemword_window_type=both&fc_lemword_wsize=5&fc_lemword=&fc_lemword_type=all&fc_pos_window_type=both&fc_pos_wsize=5&fc_pos_type=all&usesubcorp=&fsca_bncdoc.genre=&fsca_u.who=\""
		command = "./save_page.sh " + query + " --browser \"firefox\" --load-wait-time 20 --save-wait-time 10 --destination \"/home/raghav/summer/corpora/Roth/Conc" + str(i) + ".html\""
		#print command
		os.system(command)
		time.sleep(2)				
		with open("/home/raghav/summer/corpora/Roth/Conc" + str(i) + ".html", "r") as webpage:
			webpage_data="".join(line.rstrip() for line in webpage)
			list_indices = locations_of_substring(webpage_data, ">" + ID + "</td>")
			for index in list_indices:
				trunc_data = webpage_data[index + 8:]
				index_to_end = trunc_data.find("</td>")
				sentence = ""
				if (trunc_data.find("<span class=\"nott\">") < index_to_end):
					sentence += trunc_data[trunc_data.find("<span class=\"nott\">")+19:trunc_data.find("</span>")]
					trunc_data = trunc_data[trunc_data.find("</span>"):]
				
				if (trunc_data.find("<b class=\"col0 coll nott\">") < index_to_end):
					sentence += trunc_data[trunc_data.find("<b class=\"col0 coll nott\">")+26:trunc_data.find("</b>")]
					trunc_data = trunc_data[trunc_data.find("</b>"):]
				
				if (trunc_data.find("<span class=\"nott\">") < index_to_end):
					trunc_data = trunc_data[trunc_data.find("<span class=\"nott\">"):]
					sentence += trunc_data[trunc_data.find("<span class=\"nott\">")+19:trunc_data.find("</span>")]
					trunc_data = trunc_data[trunc_data.find("</span>"):]
				
				write_file = open('/home/raghav/summer/corpora/Roth/sentences_unseen', 'a')
				write_file.write(line + lvc_string + " ||| " + sentence + " ||| " + components[2] + "\n\n")
				write_file.close()
