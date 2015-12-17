while true
do
	python fetch_sentences_v2.py
	rm -rf ../../Conc*
	sleep 20
done
