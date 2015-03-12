import os, sys, math, pickle, psycopg2, ast, traceback
import numpy as np
from sklearn import cross_validation
from MTurkConnector import MTurkConnector
from abc import ABCMeta, abstractmethod, abstractproperty
from time import sleep
from random import shuffle
import my_utils

class LearningAutomation(object):
  """Enable automated active learning
  
  Learning automation coordinate machine learning object (classifier - clf) and 
  MTurkConnector instance (mc) to achieve automated active learning. 
  
  Attributes:
      project: Name of the project
      root_path: Directory of where the project related file should be stored
      clf: A classifier object classifier object to be trained 
           (need at least .fit and .predict_proba functions)
      mc: A MTurkConnector object
      u_pool: A list storing unlabeled samples [id, sample, feature]
      p_train_pool: A dict storing training samples pending for labels {id: [id, sample, feature]}
      p_test_pool: A dict storing testing samples pending for labels {id: [id, sample, feature]}
      l_train_pool: A list storing labeled training samples [id, sample, feature, label]
      l_test_pool: A list storing labeled testing samples [id, sample, feature, label]
      header: A list storing the headers of a mturk question file
      _is_diverse: A boolean indicating class diversity of l_train_pool
      useDB: A boolean indicating whether database should be used
      db: A string of database name if database is used
      db_user: A string of database user name if database is used
      db_password: A string of database user password if database is used
      logger: Logger object to perform logging operation
      recorder: Recorder object to perform important event recording
      kFoldAccuracy: a float value indicating the k-fold validation accuracy of the last iteration
      deviation: a float value indicating of deviation of the k-fold validation accuracy
      controlGroupAccuracy: a float value indicating the control group validation accuracy of the last iteration
      useDefined: A dict of user defined variable used in sample2Info and answer2Label methods
  """
  project = None
  root_path = ''
  clf = None
  mc = None
  u_pool = []
  p_train_pool = {}
  p_test_pool = {}
  l_train_pool = []
  l_test_pool = []
  header = []
  _is_diverse = False
  useDB = False
  db = ''
  db_user = ''
  db_password = ''
  logger = None
  recorder = None
  kFoldAccuracy = 0
  deviation = 0
  controlGroupAccuracy = 0
  useDefined = {}
  
  def __init__(self, project, clf, mc, useDB=False, db='', db_user='', db_password='', \
               root_path = '', unlabeled_samples = None, labeled_samples = None, \
               header = None, logger = None, recorder = None):
    """Initialize LearningAutomation class
    
    Args:
        project: Project name
        clf: Classifier object to be trained
        mc: MTurkConnector object
        useDB: A boolean indicating whether database should be used
        db: A string of database name if database is used
        db_user: A string of database user name if database is used
        db_password: A string of database user password if database is used
        root_path: A string of path to where the project related file should be stored
        unlabeled_samples: Same as u_pool. Required if samples are not loaded from database. 
        labeled_samples: Same as l_train_pool. Required if samples are not loaded from database. 
        header: A list storing the headers of a mturk question file. Set None to use auto header generation
        logger: A logger object to perform logging operation. Set None to use console print only
        recorder: A recorder object to perform important event recording.
    """
    self.logger = logger
    self.recorder = recorder
    try:
      self.logger.log('info', 'Preparing learning automation...')
      self.project = project
      self.root_path = root_path
      self.clf = clf
      self.mc = mc
      self.header = header
      self.useDB = useDB
      if self.useDB:
        self.db = db
        self.db_user = db_user
        self.db_password = db_password
        self.logger.log('info', 'Loading samples from database...')
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute('''SELECT * FROM {0}'''.format('"' + project + '_samples"'))
        rows = cur.fetchall()
        if len(rows) == 0:
          raise Exception('Samples not found.')
        else:
          for row in rows:
            temp = []
            temp.append(row[0])
            temp.append(row[1])
            temp.append(ast.literal_eval(row[2]))
            #If the row has no label, add to self.u_pool
            if row[3] is None or row[3] == '':
              self.u_pool.append(temp)
            #If the row has label, parse it and add to labeled sample pool
            else:
              temp.append(ast.literal_eval(row[3]))
              if row[5] is False:
                self.l_train_pool.append(temp)  #Add to self.l_train_pool for training
              elif row[5] is True:
                self.l_test_pool.append(temp)   #Add to self.l_test_pool for control group validation
        conn.close()
        
        #Log sample loading results
        self.logger.log('success', str(len(self.u_pool)) + ' ' + \
                        'unlabeled samples and ' + str(len(self.l_train_pool) + len(self.l_test_pool)) + ' ' + \
                        'labeled samples are loaded. (' + str(len(self.l_test_pool)) + ' of them are for testing)')
      else:
        self.u_pool = unlabeled_samples
        self.l_train_pool = labeled_samples if not labeled_samples == None else []
      
      if not self.mc is None:
        #Check mturk connector
        if not mc.check_files():
          raise Exception('Incomplete mturk connector detected.')
        
        #Check header
        self.header = self.header if not self.header == None else mc.get_auto_header()
      
      #Check integrity of unlabeled sample pool
      if not isinstance(self.u_pool, list):
        raise Exception('Unlabeled samples should be passed as a list.')
      
      #Check integrity of labeled samples and labels
      if not isinstance(self.l_train_pool, list) or not isinstance(self.u_pool, list):
        raise Exception('Labeled samples and labels should be passed as lists.')
        
      self.is_diverse()
        
      self.logger.log('success', 'Learning automation configuration completed.')
    except Exception, e:
      traceback.print_exc()
      self.logger.log('danger', 'Unexpected error: ' + e.message)
      self.logger.log('danger', 'Fail to complete learning automation configuration.')
      my_utils.exit(self.recorder)  #Exit with recording a marker
    
  def trainOnly(self):
    """Train a classifier with all labeled samples loaded
    
    Build a classifier, perform accuracy evaluation. Also predict and 
    rate all unlabeled samples by entropy but no sampling operation. 
    Used when active learning or MTurk is disabled.
    
    Returns:
        A trained classifier object
    """
    try:
      self.train_clf()
      if len(self.u_pool) > 0:
        self.rate_and_sort()
      return self.clf
    except Exception, e:
      traceback.print_exc()
      self.logger.log('danger', 'Unexpected Error: ' + e.message)
      my_utils.exit(self.recorder)

  def auto(self, hits_for_init = 10, hits_per_iter = 5, samples_per_hit = 5, \
           threshold = 2, pending = 30, stopAtAmount = 150, stopAtErrorRate = None, \
           enlargeSamplingRange = 0, controlGroupRadio = 0, need_init = True):
    """Perform automated active learning
    
    Args:
        hits_for_init: An integer of the number of hits to be create for initialization
        hits_per_iter: An integer of the number of hits to be create for each non-initial 
                       iteration
        samples_per_hit: An integer of the number of samples included in each hit. Should be 
                         consistent to the number of questions in MTurk question file
        threshold: An integer indicating that new hits will be create when number of pending 
                   hits is lower or equal to threshold
        pending: An integer of time interval in second between each query to mturk
        stopAtAmount: An interger of the amount of labeled samples indicating when to stop 
                      creating new hits
        stopAtErrorRate: A float of the error rate indicating when to stop creating new hits
        enlargeSamplingRange: An interger of the multiplicator of enlarged sampling range
        controlGroupRadio: An interger of the percentage of samples used for control 
                           group validation
        need_init: A boolean of whether initialization is need
        
    Returns:
      A trained classifier object
    """
    try:
      samples_for_init = hits_for_init * samples_per_hit
      samples_per_iter = hits_per_iter * samples_per_hit
      training_samples_amount = samples_per_iter * 100 / (100 + controlGroupRadio)
      testing_samples_amount = samples_per_iter - training_samples_amount
      
      #Remove remaining record of last terminated execution 
      self.mc.clear_trash_record()
      
      if need_init:
        self.initialization(samples_for_init, samples_per_hit, pending)
      elif not need_init and not self.is_diverse():
        self.logger.log('danger', 'Please provide labeled samples and labels to run without initialization')
        my_utils.exit(self.recorder)
      
      pending_amount = self.mc.get_pending_amount()
      
      self.rate_and_sort()
      
      while True:
        #If amount of labeled samples or error rate meet stop criteria
        if len(self.l_train_pool) + len(self.l_test_pool) >= stopAtAmount or \
           (stopAtErrorRate is not None and \
           (self.controlGroupAccuracy > stopAtErrorRate or self.kFoldAccuracy > stopAtErrorRate)):
          if len(self.l_train_pool) + len(self.l_test_pool) >= stopAtAmount:
            self.logger.log('success', 'Amount of labeled samples meets user request.')
          elif stopAtErrorRate is not None and (self.controlGroupAccuracy > stopAtErrorRate or self.kFoldAccuracy > stopAtErrorRate):
            self.logger.log('success', 'Error rate meets user request.')
          #If there are still some samples pending for answers on MTurk: Wait"
          if not pending_amount == 0:
            self.logger.log('info', 'Stop generating new HITs. Pending for last ' + str(pending_amount) + ' HITs.')
          #Else: stop execution
          else:
            break
        else:
          #Rate and sort unlabeled sample pool
          self.rate_and_sort()
          
          #Define the sampling range
          top = samples_per_iter * (enlargeSamplingRange+1) if samples_per_iter * (enlargeSamplingRange+1) < len(self.u_pool)/10 else len(self.u_pool)/10
          
          #Pick samples for training
          training_samples = self.pick_new_samples(training_samples_amount, 0, top, 'training')
          for ts in training_samples:
            self.p_train_pool[ts[0]] = ts
          
          #Pick samples for testing
          testing_samples = self.pick_new_samples(testing_samples_amount, 0, len(self.u_pool), 'testing')
          for ts in testing_samples:
            self.p_test_pool[ts[0]] = ts
            
          samples = training_samples + testing_samples
          shuffle(samples)
          
          #Generate corresponding data and upload to mturk
          id_list, data_list = self.create_id_data_pair(samples, samples_per_hit)
          amount = self.mc.upload_hits(self.header, id_list, data_list)
          
          #If no HIT can be created, stop the execution
          if amount == 0:
            self.logger.log('danger', 'Fail to create any HIT. Please check for logs for more details.')
            my_utils.exit(self.recorder)
            
        #Wait for answers
        pending_amount = self.pend_results(threshold, pending, False, False)
        
        #Update model
        self.train_clf()
        
        self.logger.log('info', 'Current labeled samples: ' + str(len(self.l_train_pool) + len(self.l_test_pool)) + ' ' + \
                        '(' + str(len(self.l_test_pool)) + ' of them are for testing.)')
        
      return self.clf
    except Exception, e:
      traceback.print_exc()
      self.logger.log('danger', 'Unexpected Error: ' + e.message)
      my_utils.exit(self.recorder)
  
  def initialization(self, number, samples_per_hits, pending):
    """Perform initialization
      
      Initialization is need if there is no labeled samples. The process 
      will randomly certain amount of samples for labeling until the diversity 
      requirement is fulfilled (that is there are some samples having different 
      labels)
      
      Args:
          number: An integer of samples to be uploaded in each attempt
          samples_per_hit: An integer of samples included in each hit. Should be 
                           coincided to number of questions in MTurk question files
          pending: An integer of the time interval in second between each query to mturk
    """
    self.logger.log('info', 'Initialization starts.')
    while not self.is_diverse():
      samples = self.pick_new_samples(number, 0, len(self.u_pool), 'initialization')
      for s in samples:
        self.p_train_pool[s[0]] = s
      
      #Generate corresponding data and upload to mturk
      id_list, data_list = self.create_id_data_pair(samples, samples_per_hits)
      self.mc.upload_hits(self.header, id_list, data_list)
      
      self.pend_results(0, pending, is_real_time = False, is_init = True)
      
    self.train_clf()
    self.logger.log('success', 'Initialization finish.')

  def pend_results(self, threshold, pending, is_real_time = False, is_init = False):
    """Pending results of upload samples
    
      Periodically check whether uploaded HITs are answered by workers 
      or not. If they are answered, retrieve the answers, parse into labels 
      and store into pool, and upgrade classifer.
      
      Args:
          threshold: An integer indicating that new hits will be create when number of pending 
                     hits is lower or equal to threshold
          pending: An integer of the time interval in second between each query to mturk
          is_real_time: A boolean indicating whether the classifier should be upgraded once some 
                        new labels are fetched or upgraded only when threshold is met
          is_init: A boolean indicating whether it is in initialization stage
          
      Returns:
          An integer of how many HITs are still pending for answers
    """
    pending_amount = threshold + 1
    while pending_amount > threshold:
      self.logger.log('info', 'Pending for results... (' + str(pending) + 's)')
      sleep(pending)
      #Call mturk connecter to check updates
      pending_amount = self.mc.update_results()
      
      #Try to get retrieved answers
      results = self.mc.get_answer()
      #If there is no new answer
      if results == None:
        print '[Msg] No labelled samples are currently available.'
        continue
      #If new answer(s) are fetched
      else:
        print '[Msg] ' + str(len(results)) + ' new labelled samples are fetched.'
        
        sample_id = []
        label = []
        hidid = []
        
        for r in results:
          #Extract sample ID
          sample_id.extend(ast.literal_eval(r[0]))
          #Extract label
          label.extend([self.answer2Label(answer) for answer in ast.literal_eval(r[1])])
          #Extract hidid
          for i in range (0, len(ast.literal_eval(r[0]))):
            hidid.append(r[2])
            
        id_label_pairs = zip(sample_id, label, hidid)
        conn = self.get_db_connection()
        cur = conn.cursor()
        for pair in id_label_pairs:
          if pair[0] in self.p_train_pool:      #Search sample in training sample pending pool
            temp = self.p_train_pool[pair[0]]   #Extract from traing sample pending pool
            del self.p_train_pool[pair[0]]      #Remove from traing sample pending pool
            temp.append(pair[1])                #Append label to list
            self.l_train_pool.append(temp)      #Append to labeled training sample pool
            cur.execute('UPDATE "{0}_samples" SET (label, label_source, for_testing) = (%s, %s, false) WHERE sample_id = {1}'.format(self.project, pair[0]), (str(pair[1]), pair[2], ))
            
          elif pair[0] in self.p_test_pool:     #Search sample in training sample pending pool
            temp = self.p_test_pool[pair[0]]
            del self.p_test_pool[pair[0]]       #Remove from traing sample pending pool
            temp.append(pair[1])                #Append label to list
            self.l_test_pool.append(temp)       #Append to labeled training sample pool
            cur.execute('UPDATE "{0}_samples" SET (label, label_source, for_testing) = (%s, %s, true) WHERE sample_id = {1}'.format(self.project, pair[0]), (str(pair[1]), pair[2], ))

        conn.commit()
        conn.close()
          
        if is_real_time:
          self.train_clf()
        
        if pending_amount > threshold:
          self.logger.log('info', str(pending_amount) + ' HITs are still pending.')
          
    return pending_amount
    
  def rate_and_sort(self):
    """Rate unlabeled samples and sort the pool according to entropy"""
    if self.is_diverse():
      self.logger.log('info', 'Calculating entropy and rating samples...')
      estimation = []
      predictions = self.clf.predict_proba([features for a,b,features in self.u_pool])
      
      #Calculate predicted sample distribution 
      try:
        classes = self.clf.classes_
        count = []
        for _class in classes:
          count.append(0)
        for p in predictions:
          i = map(lambda x: (x), p).index(max(p))   #Get prediction results
          count[i] = count[i] + 1
        estimation = zip(classes, count)
      except:
        traceback.print_exc()
        
      entropy = map(self.get_entropy, predictions)  #Calculate entropy
      
      #Sort unlabeled sample pool according to entropy
      self.u_pool = [upool for entro, upool in \
                     sorted(zip(entropy, self.u_pool), reverse=True)]
                     
      #Get the top 100 uncertain samples' id
      topU = [p[0] for p in self.u_pool[:100]]
      
      #Store the predicted sample distribution and uncertain samples' id
      try:
        evaluation = {'top100': topU, 'estimation': estimation}
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute('''UPDATE project SET sample_predict = %s where name = %s''', (str(evaluation), self.project))
        conn.commit()
        conn.close()
      except:
        traceback.print_exc()
  
  def pick_new_samples(self, number, from_index, to_index, wt_for):
    """Pick samples from the unlabeled sample pool
    
    Pick samples from the unlabeled sample pool. For example, 
    pick_new_samples(10, 0, 100, , 'initialization') means to pick 10
    samples from index 0 to 100 for initialization purpose.
    
    Args:
        number: An integer of the number of samples to be picked
        from_index: An integer of the starting index of sampling range
        to_index: An integer of the ending index of sampling range
        wt_for: A string of the purpose of sampling
        
    Returns:
        A list of samples picked from unlabeled sample pool
    """
    self.logger.log('info', 'Picking new samples...')
    #Generate a list of indices
    indices = np.random.randint(low=from_index, high=to_index, size=(number, 1)).tolist()
    
    #Pop samples from unlabeled sample pool
    samples = []
    indices = sorted(indices, reverse=True)
    for index in indices:
      sample = self.u_pool.pop(index[0])
      samples.append(sample)
    self.logger.log('info', str(number) + ' new samples are picked for ' + wt_for + '.')
    return samples
  
  def create_id_data_pair(self, samples, number):
    """Create sample id and content pair
    
    Generate contents from samples or features to be display on MTurk
    for works and create sample-id-content pair.
    
    Args:
        samples: A list of samples to be uploaded to MTurk
        number: An integer of number of samples per HIT
    
    Returns:
        A list of lists of sample and a list of lists of data
        For example, if number is 3, it returns list like:
        [[sid_0, sid_1, sid_2], [sid_3, sid_4, sid_5], ...] and
        [[data_0, data_1, data_2], [data_3, data_4, data_5], ...]
    """
    self.logger.log('info', 'Generating data from samples...')
    data = [self.sample2Info(sample[1], sample[2]) for sample in samples]
    
    if not len(data) == len(samples):
      self.logger.log('warning', 'Mismatch between data generated and samples.')
      self.logger.log('danger', 'Function sample2Info transforms samples invalidly.')
      my_utils.exit(self.recorder)
    
    id_lists = []
    data_lists = []
    
    for i in range(0, len(samples), number):
      id_list = []
      data_list = []
      for j in range (i, i + number):
        if type(data[j]) is list:     #Multiple contents for each question
          data_list.extend(data[j])
        else:                         #Single content for each question
          data_list.append(data[j])
        id_list.append(samples[j][0])
      data_lists.append(data_list)
      id_lists.append(id_list)
    
    return id_lists, data_lists
  
  def is_diverse(self):
    """Check diversity of labeled sample pool
    
    Supervised learning is possible only when samples have more than 
    one class (more than one type of label)
    
    Returns:
        A boolean of whether diversity requirement is fulfilled
    """
    l_pool = self.l_train_pool + self.l_test_pool
  
    if self._is_diverse:
      return True
    if len(l_pool) == 0:
      self._is_diverse = False
    else:
      first_label = l_pool[0][3]
      for row in l_pool:
        if not first_label == row[3]:
          self._is_diverse = True
          return True
    return self._is_diverse
  
  def train_clf(self):
    """Train the classifier
    
    Fit classifier with samples and labels to upgrade classification ability
    """
    self.logger.log('info', 'Updating classifier...')
    try:
      #Use all labeled samples for training
      l_pool = self.l_train_pool + self.l_test_pool
      features = [feature for c1, c2, feature, c4 in l_pool]
      labels = [label for c1, c2, c3, label in l_pool]
      self.get_training_errors(features, labels)
      self.clf.fit(features, labels)
      self.save()
    except Exception, e:
      traceback.print_exc()
      self.logger.log('danger', 'Unexpected error: ' + e.message)
      self.logger.log('danger', 'Failure occurs during classifier training.')
      my_utils.exit(self.recorder)
  
  def get_training_errors(self, features, labels):
    """Calculate classification accuracy
    
    Perform control group validation (if enabled) and 5-fold 
    validation (if have enough samples) to evaluate the performance 
    of the classifier
    
    Args:
        features: A list of features of samples
        labels: A list of labels of samples
        
    Returns:
        A list containing control group validation accuracy in float, 
        5-fold validation accuracy in float, and deviation of 5-fold 
        validation accuracy in float
    """
    self.logger.log('info', 'Calculating training error...')
    try:
      #Control group validation
      if len(self.l_test_pool) > 0:
        train_features = [feature for c1, c2, feature, c4 in self.l_train_pool]
        train_labels = [label for c1, c2, c3, label in self.l_train_pool]
        test_features = [feature for c1, c2, feature, c4 in self.l_test_pool]
        test_labels = [label for c1, c2, c3, label in self.l_test_pool]
        self.clf.fit(train_features, train_labels)
        classes = self.clf.classes_.tolist()
        proba = self.clf.predict_proba(test_features).tolist()
        correct = 0
        
        for test_result in zip(test_labels, proba):
          if test_result[0] == classes[test_result[1].index(max(test_result[1]))]:
            correct = correct + 1
        
        self.controlGroupAccuracy = 1.0*correct / len(test_labels)
        self.logger.log('info', 'Current control group validation accuracy: ' + \
                                '%0.2f' % (self.controlGroupAccuracy))
    
      #K-fold validation (5-fold in default)
      scores = cross_validation.cross_val_score(self.clf, features, labels, cv=5)
      self.kFoldAccuracy = scores.mean()
      self.deviation = scores.std() * 2
      self.logger.log('info', 'Current k-fold validation accuracy: ' + \
                              '%0.2f (+/- %0.2f)' % (self.kFoldAccuracy, self.deviation))
      return [self.controlGroupAccuracy, self.kFoldAccuracy, self.deviation]
    
    except Exception, e:
      traceback.print_exc()
      self.logger.log('warning', 'Cannot perform cross validation. ' + e.message)
    
    finally:
      if not self.mc is None: 
        payment = self.mc.get_total_payment()
      else:
        payment = 0
      self.recorder.record(recordType="training", \
                           controlGroupSize=len(self.l_test_pool), \
                           controlGroupAccuracy=self.controlGroupAccuracy, \
                           kFoldAccuracy=self.kFoldAccuracy, \
                           deviation=self.deviation, \
                           labeledAmount=(len(self.l_train_pool)+len(self.l_test_pool)), \
                           payment=payment)
  
  def get_entropy(self, prob_list):
    """Calculate the entropy of prediction made on each sample
    
    Calculate the Shannon Entropy on the list of probability float value, 
    with excluding any zero or negative probability returned by Decision 
    Trees or Gaussian Naive Bayes classifiers
    
    Args:
        prob_list: A list of float indicating the probability of the sample
                   belongs to a class
    
    Returns:
        A float indicating the entropy. The higher this value is, the more 
        uncertain the classifier believes on its prediction
    """
    prob_list = [ p for p in prob_list if p > 0 ]
    if len(prob_list) == 1:
      return 0
    base = len(prob_list)
    entropy = sum(map(lambda p: -p*math.log(p, base), prob_list))
    return entropy
  
  def get_db_connection(self):
    """Get a database connection"""
    return my_utils.get_db_connection(self.db, self.db_user, self.db_password)
  
  def save(self):
    """Save the classifier object as a .pkl file under the project directory"""
    with open('project/' + self.project + '/clf.pkl', 'wb') as output:
      pickle.dump(self.clf, output, pickle.HIGHEST_PROTOCOL)
  
  '''    
  def load(self, path):
    with open(path) as clfPKLFile:
      clf = pickle.load(clfPKLFile)
      self.clf = clf
      print '[Msg] Successfully loaded LearningAutomation object.'
      return clf
  '''
  
  @abstractmethod
  def sample2Info(self, sample, feature):
    """Transform sample and features to contents to be displayed on MTurk
    
    An user defined method implements how to transform samples or features to 
    the content that going to be uploaded to MTurk and displayed for workers. 
    If class scale variable is needed to be maintained, user can use a dict 
    named useDefined. e.g. useDefined['sampleCount'] = <someValue>
    
    Args:
        sample: A string containing the sample
        feature: A list of features
        
    Returns:
        A string of content to be display for the sample
    """
    raise NotImplementedError( "Should have implemented this" )
    
  @abstractmethod
  def answer2Label(self, answer):
    """Transform answer to label to be used by classifier
    
    An user defined method implements how to transform an answer of a question 
    given by a worker to a label that the classifer learns from. If class scale 
    variable is needed to be maintained, user can use a dict named useDefined. 
    e.g. useDefined['sampleCount'] = <someValue>
    
    Args:
        answer: A string containing an answer of a question given by a worker
        
    Returns:
        a value (usually integer or float) as the label of the sample for 
        classifer to learn on
    """
    raise NotImplementedError( "Should have implemented this" )
