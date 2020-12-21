import spacy
import streamlit as st
import pandas as pd
from spacy.tokens import Span
from spacy import displacy
import urllib
from utils import get_html

import spacy
import scispacy
from scispacy.linking import EntityLinker



@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_model():
    nlp = spacy.load('en_core_sci_sm')
    return nlp

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_linker():
    linker = EntityLinker(resolve_abbreviations=True, name="umls")
    return linker

@st.cache
def load_sem_types():
    path = 'https://metamap.nlm.nih.gov/Docs/SemanticTypes_2018AB.txt'
    sem_types = pd.read_csv(path, delimiter='|', names=['abrev', 'tui', 'desc'])
    return sem_types[['tui', 'desc']].set_index('tui').to_dict()['desc']


sem_types = load_sem_types()

nlp = load_model()
linker = load_linker()
try:
    nlp.add_pipe(linker)
except:
    st.write('')

def label_ents_by_tui(doc):
    new_ents = []
    for ent in doc.ents:
        try:
            cui = ent._.umls_ents[0][0]
            tui = linker.kb.cui_to_entity[cui][3][0]
            new_ent = Span(doc, ent.start, ent.end, label=sem_types[tui])
            new_ents.append(new_ent)
        except:
            new_label = 'other'
            new_ent = Span(doc, ent.start, ent.end, label=new_label)
            new_ents.append(new_ent)
    doc.ents = new_ents
    return doc

try:
    nlp.add_pipe(label_ents_by_tui)
except:
    st.write('')



text = st.text_area(
    'Text', "Past medical history includes hypertension, dyslipidemia and diabetes, and a family history of coronary artery disease. He started having chest pain 4 hours ago, associated with dyspnea, nausea, and diaphoresis.")

doc = nlp(text)

# disabled.restore()
# target_labels = ['Finding', 'Disease or Syndrome',
#                  'Sign or Symptom', 'Pathologic Function', 'Neoplastic Process', 'Other']

# st.write(doc.ents)

# for ent in doc.ents:
#     st.write(ent.text, ' - ', ent.label_)


html = displacy.render(
    doc, style="ent",
    options={
        "ents": ['FINDING', 'DISEASE OR SYNDROME',
                 'SIGN OR SYMPTOM', 'PATHOLOGIC FUNCTION', 'NEOPLASTIC PROCESS', 'OTHER'],
        "colors": {'FINDING': '#D0ECE7', 'DISEASE OR SYNDROME': '#D6EAF8',
                   'SIGN OR SYMPTOM': '#E8DAEF', 'PATHOLOGIC FUNCTION': '#FADBD8', 'NEOPLASTIC PROCESS': '#DAF7A6'}
    }
)
style = "<style>mark.entity { display: inline-block }</style>"
st.write(f"{style}{get_html(html)}", unsafe_allow_html=True)

data = [
    [str(getattr(ent, attr)) for attr in ["text", "label_", "start", "end", "start_char", "end_char"]
     ]
    for ent in doc.ents
    # if ent.label_ in target_labels
]
df = pd.DataFrame(data, columns=["text", "label_", "start", "end", "start_char", "end_char"]
                  )
st.dataframe(df)

