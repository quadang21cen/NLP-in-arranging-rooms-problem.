from sklearn.metrics.pairwise import cosine_similarity
from underthesea import text_normalize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import string
import numpy as np
from sklearn.model_selection import train_test_split
import seaborn as sns
class TF_IDF_class:
    def __init__(self) -> None:
        self.stopwords_path = "vietnamese_stopwords.txt"

    def get_stopwords_list(self, stop_file_path):
        """load stop words """

        with open(stop_file_path, 'r', encoding="utf-8") as f:
            stopwords = f.readlines()
            stop_set = set(m.strip() for m in stopwords)
            return list(frozenset(stop_set))

    def tokenize_vn(self, doc):
        # Tokenize the words
        normalized_doc = text_normalize(doc)
        doc = word_tokenize(normalized_doc)
        # Remove Punctuation (VD: Xoa dau !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ )
        punctuation = string.punctuation
        clean_words = [w for w in doc if w not in punctuation]
        clean_words = [w for w in clean_words if (" " in w) or w.isalpha()]
        return clean_words
    def transform_vector(self, text_list):
        # Create TfidfVectorizer for Vietnamese
        stop_words_list = self.get_stopwords_list(self.stopwords_path)
        vect = TfidfVectorizer(tokenizer=self.tokenize_vn, stop_words=stop_words_list, lowercase=True, ngram_range=(1,3), max_features=3000,sublinear_tf=True)
        tfidf = vect.fit_transform(text_list)
        return vect,tfidf
    def text2vec(self, text_list):
        vect, tfidf = self.transform_vector(text_list)
        arrays = [value for value in tfidf.toarray()]
        return arrays
    def pairwise(self, matrix):
        return cosine_similarity(matrix, matrix)
    def compare_vectors(self, vec1, vec2):
        return cosine_similarity([vec1], [vec2])

import pandas as pd
df = pd.read_csv('Student_Ins.csv')
features = ["Timestamp", "Name", "Sex", "Hometown", "Major", "Bio_personality", "food_drink", "hobby_interests",
                             "smoking", "refer_roommate", "Cleanliess", "Privacy", "Unnamed"]
df.columns = features


corpus = ["tôi  thích bơi lội,nghe nhạc, và đọc sách",
            "Toi thich da bong"
           ]


#label_id_df = df['labels'].drop_duplicates()
#label_to_id = dict(label_id_df.values)
#id_to_label = dict(label_id_df[['label_id','Label']].values)
from matplotlib import pyplot as plt
def plot():
    fig = plt.figure(figsize=(10,10))
    df.groupby('labels').Bio_personality.count().sort_values().plot.barh(ylim =0, title= 'Number of records per label\n')
    plt.xlabel('Number of records.')
    #plt.show()
plot()
# stop_words_list = get_stopwords_list(".\\vietnamese_stopwords.txt")
# vect = TfidfVectorizer(tokenizer=tokenize_vn, stop_words=stop_words_list, lowercase = True)
# tfidf = vect.fit_transform(corpus)

tf_idf = TF_IDF_class()
vect, tfidf = tf_idf.transform_vector(df['Bio_personality'])

import pandas as pd
feature_df = pd.DataFrame(tfidf.todense(),
                        columns=vect.get_feature_names_out())

feature_df.to_csv("test.csv")

pairwise_similarity = tfidf * tfidf.T 
matrix = tf_idf.text2vec(df['Bio_personality'])
print(tf_idf.pairwise(matrix))
cosine_similarity_pd = pd.DataFrame(tf_idf.pairwise(matrix), columns = [*range(len(matrix))])
print(cosine_similarity_pd)

# Đánh giá độ chính xác bằng text classification
import random
df["labels"] = [random.randint(0, 5) for _ in range(len(df['Bio_personality']))]

from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from xgboost import XGBClassifier
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score
models = [
    RandomForestClassifier(n_estimators=100, max_depth=5, random_state=0),
    XGBClassifier(),
    LinearSVC(),
    MultinomialNB()
]

labels = df.labels

cross_value_scored = []
for model in models:
    model_name = model.__class__.__name__
    accuracies= cross_val_score(model, matrix, labels, scoring = 'accuracy', cv = 5)
    for accuracy in accuracies:
        cross_value_scored.append((model_name, accuracy))

df_cv = pd.DataFrame(cross_value_scored, columns =['model_name', 'accuracy'])
acc = pd.concat([df_cv.groupby('model_name').accuracy.mean(),df_cv.groupby('model_name').accuracy.std()], axis= 1,ignore_index=True)
acc.columns = ['Mean Accuracy', 'Standard deviation']
print(acc)

# hyperparameter tunning of XGBClassifier
clf_xgb = XGBClassifier()
# hypermeter setting
param_dist = {'n_estimators': np.random.randint(150, 500,100),
              'learning_rate': [0.01,0.1,0.2,0.3,0.4, 0.59],
              'max_depth': [3, 4, 5, 6, 7, 8, 9],
              'min_child_weight': [1, 2, 3, 4]
             }
from sklearn.model_selection import KFold
kfold_5 = KFold(shuffle = True, n_splits = 5)

from sklearn.model_selection import RandomizedSearchCV
clf = RandomizedSearchCV(clf_xgb,
                         param_distributions = param_dist,
                         cv = kfold_5,
                         n_iter = 5,
                         scoring = 'roc_auc',
                         verbose = 3,
                         n_jobs = -1)

# spliting the data into test and train
x_train, x_test, y_train, y_test = train_test_split(matrix, labels, random_state=0, test_size=0.2)

# creating and fiting the instance of the xgb classifier
xgb = XGBClassifier()
xgb.fit(x_train,y_train)

XGBClassifier(base_score=0.5, booster='gbtree', colsample_bylevel=1,
              colsample_bynode=1, colsample_bytree=1, gamma=0, gpu_id=-1,
              importance_type='gain', interaction_constraints='',
              learning_rate=0.300000012, max_delta_step=0, max_depth=6,
              min_child_weight=1, monotone_constraints='()',
              n_estimators=100, n_jobs=4, num_parallel_tree=1,
              objective='multi:softprob', random_state=0, reg_alpha=0,
              reg_lambda=1, scale_pos_weight=None, subsample=1,
              tree_method='exact', validate_parameters=1, verbosity=None)

y_pred = xgb.predict(x_test)

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
print('Classification report')
print(classification_report(y_test, y_pred))

# confusion_matrx
# conf_matrix = confusion_matrix(y_test, y_pred)
# fig, ax = plt.subplots(figsize=(11,11))
# label_id_df = df[['labels', "Bio_personality"]].drop_duplicates()
# sns.heatmap(conf_matrix, annot=True, cmap = 'Reds', fmt='d',xticklabels = label_id_df.labels.values,
#            yticklabels = label_id_df.labels.values,square = True )
# plt.ylabel('Actual')
# plt.xlabel('Predicted')
# plt.title('Confusion Matrix.')
plt.show()

print('Accuracy of the model {}'.format(accuracy_score(y_test, y_pred)))