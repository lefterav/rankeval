

Ranking evaluation script. This script is written for the purposes of Quality Estimation Ranking 
in the field of Machine Translation, but it could in principle work for other tasks[1]. It also adopts 
a few metrics from the IR ranking shared task organized by Yahoo a few years ago. This script is under
testing and development, so please refer to the source file for further explanations and citations  


Requirements:
Set your PYTHONPATH to the src/ directory
Python 2.7 with numpy 

 

Example commadline :

python src/evaluation/rankeval.py myfile.jcml predicted_rank rank

'predicted_rank' and 'rank' are the names of the rank attribute on the sentence level. 
Before running the script you should add the rank your QE predicted in the XML element of the target 
sentence. It should therefore look like

<judgedsentence ...>
    <src ...>...</src>
    <tgt rank='1' predicted_rank='3' ..></tgt>
	<tgt rank='2' predicted_rank='4' ..></tgt>
	...
</judgedsentence>


There is also a iPython notebook that demonstrates how to use it for tasks outside of Machine Translation.

Hipster Machine Learning Metrics Made Easy
http://nbviewer.ipython.org/gist/waylonflinn/8338948

Author: Eleftherios Avramidis
License: GNU
