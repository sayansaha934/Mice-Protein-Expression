"""
This is the Entry point for Training the Machine Learning Model.

Written By: Sayan Saha
Version: 1.0
Revisions: None

"""


# Doing the necessary imports
from sklearn.model_selection import train_test_split
from data_ingestion import data_loader
from data_preprocessing import preprocessing
from data_preprocessing import clustering
from best_model_finder import tuner
from file_operations import file_methods
from application_logging import logger

#Creating the common Logging object


class trainModel:

    def __init__(self):
        self.log_writer = logger.App_Logger()
        self.db='training_logs'
        self.table_name='ModelTrainingLog'
        self.log_writer.createTableForLogging(self.db, self.table_name)


    def trainingModel(self):
        # Logging the start of Training
        self.log_writer.log(self.db, self.table_name, 'INFO' ,'Start of Training')
        try:
            # Getting the data from the source
            data_getter=data_loader.Data_Getter(self.db, self.table_name, self.log_writer)
            data=data_getter.get_data()


            """doing the data preprocessing"""

            preprocessor=preprocessing.Preprocessor(self.db, self.table_name, self.log_writer)

            #removing unwanted columns as discussed in the EDA part in ipynb file
            data = preprocessor.dropUnnecessaryColumns(data,['MouseID'])



            # get encoded values for categorical data

            data = preprocessor.encodeCategoricalValues(data)

            # create separate features and labels
            X,Y=preprocessor.separate_label_feature(data,label_column_name='class')

            # check if missing values are present in the dataset
            is_null_present=preprocessor.is_null_present(X)


            # if missing values are there, replace them appropriately.
            if(is_null_present):
                X=preprocessor.impute_missing_values(X) # missing value imputation


            """ Applying the clustering approach"""

            kmeans=clustering.KMeansClustering(self.db, self.table_name, self.log_writer) # object initialization.
            number_of_clusters=kmeans.elbow_plot(X)  #  using the elbow plot to find the number of optimum clusters

            # Divide the data into clusters
            X=kmeans.create_clusters(X,number_of_clusters)

            #create a new column in the dataset consisting of the corresponding cluster assignments.
            X['Labels']=Y

            # getting the unique clusters from our dataset
            list_of_clusters=X['Cluster'].unique()

            """parsing all the clusters and looking for the best ML algorithm to fit on individual cluster"""

            for i in list_of_clusters:
                cluster_data=X[X['Cluster']==i] # filter the data for one cluster

                # Prepare the feature and Label columns
                cluster_features=cluster_data.drop(['Labels','Cluster'],axis=1)
                cluster_label= cluster_data['Labels']

                # splitting the data into training and test set for each cluster one by one
                x_train, x_test, y_train, y_test = train_test_split(cluster_features, cluster_label, test_size=1/3, random_state=355)

                model_finder=tuner.Model_Finder(self.db, self.table_name, self.log_writer) # object initialization

                #getting the best model for each of the clusters
                best_model_name,best_model=model_finder.get_best_model(x_train,y_train,x_test,y_test)

                #saving the best model to the directory.
                file_op = file_methods.File_Operation(self.db, self.table_name, self.log_writer)
                save_model=file_op.save_model(best_model,best_model_name+str(i))

            # logging the successful Training
            self.log_writer.log(self.db, self.table_name, 'INFO', 'Successful End of Training')

        except Exception as e:
            # logging the unsuccessful Training
            self.log_writer.log(self.db,  self.table_name, 'ERROR', 'Unsuccessful End of Training')
            raise e