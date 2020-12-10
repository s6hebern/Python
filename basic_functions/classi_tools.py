import os
import time
import datetime
import itertools
import multiprocessing
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from tqdm import tqdm
from simpledbf import Dbf5
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.externals import joblib
from sklearn.preprocessing import scale
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, MiniBatchKMeans, MeanShift, Birch
from sklearn.mixture import GaussianMixture
from sklearn import metrics


class EoRandomForestClassifier:
    def __init__(self):
        self.start = time.time()
        self.inputfile = None
        self.n_training_features = None
        self.n_total_features = None
        self.training = None
        self.training_attribute = None
        self.prediction = None
        self.n_nonclassified_features = None
        self.labels = None
        self.params = None
        self.model = None
        self.cores = None
        self.importances = None

    @staticmethod
    def read_dbf(dbf_file, exclude_columns=None):
        # type: (str, list) -> pd.DataFrame
        """
        Read dbf into a pandas data frame

        :param dbf_file: Path to dbf
        :param exclude_columns: List of strings containing column names that shall be excluded. Case sensitive!
        :return: Pandas data frame containing the dbf data
        """
        dbf = Dbf5(dbf_file)
        df = dbf.to_dataframe()
        if exclude_columns:
            df = df.loc[:, df.columns.difference(exclude_columns)]
        return df

    def train(self, values, training, model, overwrite=False, silent=True):
        # type: (np.array, np.array, str, bool, bool) -> None
        """
        Train a Random Forest Classifier. See
        https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier
        for details.

        :param values: Numpy-conform array with values / characteristics
        :param training: Numpy-conform array with class / training values
        :param model: Path to output model
        :param overwrite: Overwrite model if the file already exists
        :param silent: Suppress prints
        :return: --
        """
        if not self.cores:
            self.cores = (multiprocessing.cpu_count() / 2. - 1) * 2 if multiprocessing.cpu_count() >= 4 else 1
        if not silent:
            verbosity = 2
        else:
            verbosity = 0
        if not os.path.exists(os.path.dirname(model)):
            os.makedirs(os.path.dirname(model))
        if os.path.exists(model) and overwrite is True:
            os.remove(model)
        elif os.path.exists(model) and overwrite is False:
            raise OSError('File {m} already exists and shall not be overwritten! Use option overwrite=True or choose '
                          'another name!'.format(m=model))
        if not self.params:
            # start grid search
            self.params = {'n_estimators': [100, 500, 1000, 1500, 2000],
                           'max_depth': [len(self.labels) / 4, len(self.labels) / 3, len(self.labels) / 2,
                                         len(self.labels) * 2 / 3, len(self.labels) * 3 / 4, len(self.labels), None],
                           'n_jobs': [self.cores]}
            if not silent:
                print('Starting grid search! Please be patient, this may take a while!')
            grid_search_start = time.time()
            try:
                gs = GridSearchCV(RandomForestClassifier(), self.params, cv=len(self.labels), verbose=verbosity)
            except:
                raise ValueError('Failed to assign parameters to GridSearchCV! Check arguments and try again!')
            gs.fit(values, training)
            if not silent:
                print('Best model params:')
                for key in gs.best_params_.keys():
                    print('\t{p}'.format(p=': '.join([key, str(gs.best_params_[key])])))
                print('\n\tDuration (hh:mm:ss): {t}'.format(t=datetime.timedelta(seconds=time.time() - grid_search_start)))
            self.params = gs.best_params_
            # end of grid search
        if not silent:
            print('Training model...')
        rfc = RandomForestClassifier(n_estimators=self.params['n_estimators'], criterion='gini',
                                     max_depth=self.params['max_depth'], n_jobs=self.cores, verbose=1)
        rfc = rfc.fit(values, training)
        self.importances = rfc.feature_importances_
        joblib.dump(rfc, model)
        if not silent:
            print('\tModel saved to {m}'.format(m=model))
        return

    def classify(self, training_data, attribute_field, unknown_data, model, id_column='ID', params=None, cores=None,
                 probability_threshold=None, silent=True, overwrite=False):
        # type: (pd.DataFrame, str, pd.DataFrame, str, str, dict, int, float, bool, bool) -> pd.DataFrame
        """
        Classify an array using an existing model

        :param training_data: Pandas data frame holding training data
        :param attribute_field: Attribute field holding the (numeric) classes
        :param unknown_data: Pandas data frame holding all data to be classified
        :param model: Model output name
        :param id_column: Column name holding the unique feature ID
        :param params: Dictionary with Random Forest Classifier parameters.
        :param cores: Number of cores to use.
        :param probability_threshold: If the maximum class probability is below that value, 0 will be assigned
        :param silent: Reduce print messages to a minimum
        :param overwrite: Overwrite output in case it already exists
        :return: Pandas data frame holding the results
        """
        self.training_attribute = attribute_field
        self.model = model
        self.params = params
        self.cores = cores
        try:
            training_data = training_data.astype({attribute_field: int})
        except:
            raise AttributeError('Unable to convert column {col} to int!'.format(col=attribute_field))
        self.labels = set(training_data[attribute_field])
        self.n_training_features = len(training_data)
        self.n_total_features = len(unknown_data)
        if not silent:
            print('\tTraining data contain {x} features for {y} classes'.format(x=len(training_data),
                                                                                y=len(self.labels)))
        result = unknown_data[[id_column]].copy()
        self.train(values=training_data.loc[:, training_data.columns.difference([attribute_field, id_column])],
                   training=training_data.loc[:, attribute_field], model=self.model, overwrite=overwrite, silent=silent)
        if not silent:
            print('Classifying...')
        clf = joblib.load(self.model)
        data = unknown_data.loc[:, unknown_data.columns.difference([id_column])]
        __prediction = clf.predict(data)
        proba = clf.predict_proba(data)
        self.n_nonclassified_features = 0
        if probability_threshold:
            prediction = np.zeros_like(__prediction)
            for i in tqdm(np.arange(len(prediction)), 'Progress'):
                if np.amax(proba[i]) >= probability_threshold:
                    prediction[i] = clf.classes_[np.where(proba[i] == np.amax(proba[i]))][0]
                else:
                    prediction[i] = 0
                    self.n_nonclassified_features += 1
        else:
            prediction = __prediction.copy()
        result = result.assign(PRED=pd.Series(prediction).values)
        result = result.assign(PROBA=pd.Series(np.max(proba, axis=1)).values)
        if not silent:
            print('\tDone!')
        return result

    @staticmethod
    def join_columns(df_a, df_b, prefix='', exclude_columns=None):
        # type: (pd.DataFrame, pd.DataFrame, str, list) -> pd.DataFrame
        """
        Join all columns of two data frames with the same number of entries

        :param df_a: First data frame
        :param df_b: Second data frame
        :param prefix: Prefix for column names of second data frame if they shall be renamed for the join
        :param exclude_columns: List of column names to exclude from second data frame
        :return: Joined data frame
        """
        if len(df_a) != len(df_b):
            raise AssertionError('Input data frames do not have the same number of rows!')
        if exclude_columns:
            df_b = df_b.loc[:, df_b.columns.difference(exclude_columns)]
        df_b.columns = [(prefix + c) for c in list(df_b.columns)]
        joined = df_a.copy()
        for c in df_b.columns:
            joined = joined.assign(x=pd.Series(df_b[c]).values)
        return joined

    def create_report(self, show=False, export=None):
        # type: (bool, str) -> None
        """
        Re-formats the internal parameters kappa, accuracy and the report for printing and exporting

        :param show: Prints the report to stdout
        :param export: Exports the report to the given file
        :return: --
        """
        formatted_output = list()
        formatted_output.append('#------------------------------------------------------------------------------#\n')
        formatted_output.append('\nDate / Time: {dt}\n\n'.format(dt=datetime.datetime.today().strftime(
            '%Y-%m-%d %H:%M:%S')))
        formatted_output.append('Input File: \t\t\t\t\t\t{f}\n'.format(f=self.inputfile))
        formatted_output.append('\tNo. of features: \t\t\t\t{n}\n'.format(n=self.n_total_features))
        formatted_output.append('\tNo. of classified features: \t{n}\n\n'.format(
            n=self.n_total_features - self.n_nonclassified_features))
        formatted_output.append('Training Data: \t\t\t\t\t\t{f}\n'.format(f=self.training))
        formatted_output.append('\tNo. of features: \t\t\t\t{n}\n'.format(n=self.n_training_features))
        formatted_output.append('\tTraining Attribute: \t\t\t{f}\n'.format(f=self.training_attribute))
        formatted_output.append('\tNo. of classes: \t\t\t\t{n}\n\n'.format(n=len(self.labels)))
        formatted_output.append('Output File: \t\t\t\t\t\t{f}\n\n'.format(f=self.prediction))
        formatted_output.append('\nRandom Forest Parameters:\n')
        formatted_output.append('-------------------------\n\n')
        formatted_output.append('\tn_estimators: \t{n}\n'.format(n=self.params['n_estimators']))
        formatted_output.append('\tmax_depth: \t\t{m}\n\n'.format(m=self.params['max_depth']))
        formatted_output.append('\nFeature Importances:\n')
        formatted_output.append('--------------------\n\n')
        for i, score in enumerate(self.importances):
            formatted_output.append('\tFeature {n: >{spacing}}:\t{s}\n'.format(n=i + 1,
                                                                               spacing=len(str(len(self.importances))),
                                                                               s=round(score, 4)))
        formatted_output.append('\nTotal Runtime (hh:mm:ss): \t{t}\n'.format(t=datetime.timedelta(
            seconds=time.time() - self.start)))
        formatted_output.append('\n#--------------------------------------------------------------------------------#')
        if export:
            if not os.path.exists(os.path.dirname(export)):
                os.makedirs(os.path.dirname(export))
            with open(export, 'w') as txt:
                txt.writelines(formatted_output)
        if show:
            for line in formatted_output:
                print(line.strip('\n'))
        return

#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#

def calculate_pc(df,  num_pc=None):
    # type: (pd.DataFrame, int) -> pd.DataFrame
    """
    Calculate principal components for a Pandas data frame

    :param df: Pandas data frame holding the data to be analysed
    :param num_pc: Number of principal components to return. Default is the same amount of attributes as the input data
    :return: Pandas data frame holding the principal components values in descending order
    """
    pc = PCA().fit_transform(scale(df))
    pc = pd.DataFrame(pc)
    pc.columns = ['_'.join(['pc', str(i)]) for i in range(1, len(pc.columns) + 1)]
    if num_pc:
        pc = pc.drop(pc.columns[list(range(int(num_pc), len(pc.columns)))], axis=1)
    return pc


def clustering(df, classnum, id_column, out_csv=None, mode='minibatch', pca=False, num_pc=None, cpus=1):
    # type: (str, int, str, str, str, bool, int, int) -> pd.DataFrame
    """
    Unsupervised classification of data stored in a Pandas data frame

    :param df: Dbf file holding the data to be classified
    :param classnum: Target class number (ignored for mode "meanshift")
    :param id_column: Column name holding the unique feature ID
    :param out_csv: Output file (*.csv)
    :param mode: Clustering algorithm. One of "kmeans", "minibatch" (default), "meanshift", "gaussian" or "birch". See
            https://scikit-learn.org/stable/modules/clustering.html#clustering for more details
    :param pca: Calculate principal components first and run the clustering on them
    :param num_pc: Number of principcal components to use
    :param cpus: Number of cores to use (only for mode "meanshift")
    :return: Pandas data frame holding the assigned classes
    """
    df = EoRandomForestClassifier().read_dbf(df)
    df = df.fillna(0)
    classify = df.loc[:, df.columns.difference([id_column])]
    if pca and num_pc and num_pc > len(classify.columns):
        raise ValueError('"num_pc" exceeds number of columns!')
    if pca:
        classify = calculate_pc(classify, num_pc)
    # k-means
    if mode.lower() == 'kmeans':
        kmeans = KMeans(n_clusters=classnum, random_state=0).fit(classify)
        prediction = kmeans.predict(classify)
        result = df[[id_column]].copy()
        result = result.assign(PRED=pd.Series(prediction).values)
        if out_csv:
            result.to_csv(out_csv, index=False)
    # mini batch k-means
    elif mode.lower() == 'minibatch':
        kmeans = MiniBatchKMeans(n_clusters=classnum, random_state=0, batch_size=1000, max_iter=500,
                                 reassignment_ratio=0.0025).fit(classify)
        prediction = kmeans.predict(classify)
        result = df[[id_column]].copy()
        result = result.assign(PRED=pd.Series(prediction).values)
        if out_csv:
            result.to_csv(out_csv, index=False)
    # mean shift
    elif mode.lower() == 'meanshift':
        ms = MeanShift(n_jobs=cpus).fit(classify)
        result = df[[id_column]].copy()
        result = result.assign(PRED=pd.Series(ms.labels_).values)
        if out_csv:
            result.to_csv(out_csv, index=False)
    # gaussian mixture model
    elif mode.lower() == 'gaussian':
        gauss = GaussianMixture(n_components=classnum).fit(classify)
        prediction = gauss.predict(classify)
        result = df[[id_column]].copy()
        result = result.assign(PRED=pd.Series(prediction).values)
        if out_csv:
            result.to_csv(out_csv, index=False)
    # birch
    elif mode.lower() == 'birch':
        birch = Birch(n_clusters=classnum).fit(classify)
        prediction = birch.predict(classify)
        result = df[[id_column]].copy()
        result = result.assign(PRED=pd.Series(prediction).values)
        if out_csv:
            result.to_csv(out_csv, index=False)
    else:
        raise ValueError('Mode {m} is not supported!'.format(m=mode))
    return result


def show_confusion_matrix(matrix, labels, accuracy=None, kappa=None, f_score=None, show=True, save=None):
    # type: (metrics.confusion_matrix, list, float, float, float, bool, str) -> None
    """
    Show (and save) a pre-calculated confusion matrix as a colored plot

    :param matrix: Confusion matrix as calculated by sklearn.metrics.confusion_matrix
    :param labels: Class labels that are contained in the confusion matrix
    :param accuracy: Include accurady measure
    :param kappa: Include kappa coefficient
    :param f_score: Include F-Score
    :param show: Show the confusion matrix
    :param save: Export image (file path)
    :return: --
    """
    np.set_printoptions(precision=2)
    fig = plt.figure(figsize=(len(labels), len(labels)))
    cmap = plt.cm.Blues
    plt.imshow(matrix, interpolation='nearest', cmap=cmap)
    plt.title('Confusion-Matrix')
    plt.colorbar()
    ticks = np.arange(len(labels))
    plt.xticks(ticks, labels, rotation=45)
    plt.yticks(ticks, labels)
    # label cells with counts
    for i, j in itertools.product(range(matrix.shape[0]), range(matrix.shape[1])):
        plt.text(j, i, matrix[i, j], horizontalalignment='center', color='black', linespacing=0.8)
    plt.ylabel('Truth')
    plt.xlabel('Prediction')
    if accuracy:
        plt.text(0, -2.5, 'Accuracy: {a}'.format(a=round(accuracy, 2)))
    if kappa:
        plt.text(0, -2, 'Kappa: {k}'.format(k=round(kappa, 2)))
    if f_score:
        plt.text(0, -1.5, 'Mean F1: {f}'.format(f=round(f_score, 2)))
    plt.text(0, -1, 'n: {n}'.format(n=np.sum(matrix)))
    plt.tight_layout()
    if show:
        plt.show()
    if save:
        fig.savefig(save)
    return


def create_confusion_matrix(truth, prediction, labels):
    # type: (np.array, np.array, np.array) -> np.array
    """
    Create a confusion matrix from two arrays with the same dimensions

    :param truth: Array holding truth values
    :param prediction: Array holding predicted values
    :param labels: Labels for the different classes
    :return: Confusion matrix
    """
    cm = metrics.confusion_matrix(truth, prediction, labels=labels)
    return cm


def read_validation_table(filepath, truth_column, prediction_columm, sep=','):
    # type: (str, str, str, str) -> pd.DataFrame
    """
    Read tabular data (e.g. a *.csv file) with truth and prediction attributes into a Pandas data frame

    :param filepath: Input file
    :param truth_column: Field name for truth values
    :param prediction_columm: Field name for prediction values
    :param sep: Column separator in the file
    :return: Pandas data frame holding the attributes "truth" and "prediction"
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    lines = [l.split(sep) for l in lines]
    header = lines[0]
    truth_column_index = header.index(truth_column)
    prediction_columm_index = header.index(prediction_columm)
    df = pd.DataFrame(columns=['truth', 'prediction'])
    for l in lines:
        df.loc['truth'] = l[truth_column_index]
        df.loc['prediction'] = l[prediction_columm_index]
    df = df['truth'].astype('int')
    df = df['prediction'].astype('int')
    return df, sorted(list(set(df['truth'])))


def create_report(truth, prediction, labels, confusion_matrix, show=False, save=None):
    # type: (pd.DataFrame, pd.DataFrame, list, metrics.confusion_matrix, bool, str) -> (float, float, metrics.classification_report)
    """
    Create a validation report from two datasets of the same length

    :param truth: Pandas data frame column holding the truth values
    :param prediction: Pandas data frame column holding the predicted values
    :param labels: Labels for the different classes
    :param confusion_matrix: Confusion matrix, generated from module sklearn.metric.confusion_matrix
    :param show: Print the report to stdout
    :param save: File path to save the report as a physical file (*.txt)
    :return: Tuple of kappa coefficient, overall accuracy and the generated report
    """
    kappa = metrics.cohen_kappa_score(truth, prediction, labels=labels)
    accuracy = metrics.accuracy_score(truth, prediction)
    report = metrics.classification_report(truth, prediction, labels=labels)
    formatted_output = list()
    formatted_output.append('#------------------------------------------------------------------------------#\n')
    formatted_output.append('\nDate / Time: {dt}\n\n'.format(dt=datetime.datetime.today().strftime(
        '%Y-%m-%d %H:%M:%S')))
    formatted_output.append('------------------\n')
    formatted_output.append('Scores:\n')
    formatted_output.append('-------\n\n')
    formatted_output.append('\tKappa: \t\t\t\t{k}\n'.format(k=round(kappa, 2)))
    formatted_output.append('\tAccuracy: \t\t\t{a}\n'.format(a=round(accuracy, 2)))
    formatted_output.append('\tObservations: \t\t{n}\n\n'.format(n=np.sum(confusion_matrix)))
    formatted_output.append('Report: \n')
    formatted_output.append('-------\n')
    formatted_output.append('{r}\n'.format(r=report))
    formatted_output.append('Confusion Matrix:\n')
    formatted_output.append('-----------------\n\n')
    max_length = max([len(str(l)) for l in labels]) + 4
    formatted_output.append('\tPrediction \t{line}\n'.format(line=' '.join(
        ['{a: >{spacing}}'.format(a=l, spacing=max_length) for l in labels])))
    formatted_output.append('\t{a: >{spacing}}\n'.format(a='Truth', spacing=max_length))
    for r, row in enumerate(confusion_matrix):
        formatted_output.append('\t{lab: >{spacing}}\t\t{line}\n'.format(
            lab=labels[r], spacing=max_length,
            line=' '.join(['{a: >{spacing}}'.format(a=v, spacing=max_length) for v in row])))
    formatted_output.append('\n#--------------------------------------------------------------------------------#')
    if save:
        if not os.path.exists(os.path.dirname(save)):
            os.makedirs(os.path.dirname(save))
        with open(save, 'w') as txt:
            txt.writelines(formatted_output)
    if show:
        for line in formatted_output:
            print(line.strip('\n'))
    return kappa, accuracy, report
