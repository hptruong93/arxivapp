import logging
import argparse
import numpy as np
#import numexpr as ne
import os
import scipy.sparse as scs
import scipy.optimize as sco
import multiprocessing
import time

from joblib import Parallel, delayed
from pdb import set_trace

logger = logging.getLogger(__name__)
np.random.seed(0)

root='/home/statler/lcharlin/'

def load_data(dir):
  train = np.loadtxt(os.path.join(dir,'train.tsv'),dtype=np.int32)
  valid = np.loadtxt(os.path.join(dir,'validation.tsv'),dtype=np.int32)
  test = np.loadtxt(os.path.join(dir,'test.tsv'),dtype=np.int32)

  # 0-index it
  # idx0_user = False
  # idx0_item = False
  # if np.min(train[:,0]) == 1:
  #   train[:,0] -= 1
  #   valid[:,0] -= 1
  #   test[:,0] -= 1
  #   idx0_user = True
  # if np.min(train[:,1]) == 1:
  #   train[:,1] -= 1
  #   valid[:,1] -= 1
  #   test[:,1] -= 1
  #   idx0_item = True
  #Assume 0 index since we cannot infer anything from a parse matrix
  idx0_user = True
  idx0_item = True

  train[:,2] = (train[:,2]>0)#*10
  valid[:,2] = (valid[:,2]>0)#*10
  test[:,2] = (test[:,2]>0)#*10

  d = np.vstack([train, valid, test])

  nusers = int(np.max(d[:,0]))+1
  nitems = int(np.max(d[:,1]))+1

  logger.info('+ read data from %s', dir)
  logger.info('+ nusers %s nitems %s', nusers, nitems)
  return nusers, nitems, train, valid, test, idx0_user, idx0_item

def to_mat(d, nusers, nitems):
  mat_row = scs.csr_matrix((d[:,2], (d[:,0], d[:,1])), shape=(nusers, nitems))#.toarray()
  mat_col = scs.csc_matrix((d[:,2], (d[:,0], d[:,1])), shape=(nusers, nitems))#.toarray()
  return mat_row, mat_col

def optimize(m, train_data, valid_data, nusers, nitems, T, max_iters=2):#np.inf):

  train_data_row, train_data_col = to_mat(train_data, nusers, nitems)
  valid_data_row, valid_data_col = to_mat(valid_data, nusers, nitems)

  m.save(train_data_row, train_data_col)

  iter = 0
  verr_old = np.inf
  while True and iter < max_iters:
    if iter < 5 or iter % 5 == 0:
      trerr = m.mse_err(train_data)
      verr = m.mse_err(valid_data)
      #vprec, _, num_users = m.prec_err(valid_data_row, train_data_row, T=T)
      #vmar, num_users = m.mar_err(valid_data_row, train_data_row)
      vmrr, num_users = m.mrr_err(valid_data_row, train_data_row)
      logger.info('%d: train mse: %f, valid mse: %f, valid mrr (%d users): %f' % (iter, trerr, verr, num_users, vmrr))
    if iter % 10 == 0 and iter != 0:
      m.save(train_data_row, train_data_col)

    m.update_u(train_data_row)
    #m.update_v(train_data_col)

    if verr/verr_old > 1.01:
      m.save(train_data_row, train_data_col)
      break
    verr_old = verr

    iter += 1


def run(m, train_data, valid_data, test_data, nusers, nitems, T, test_only=False, save_model = False):

  if not test_only:
    logger.info('+ optimize model')
    try:
      optimize(m, train_data, valid_data, nusers, nitems, T)
    except KeyboardInterrupt:
      logger.info('started shutdown procedures')
      optimize(m, train_data, valid_data, nusers, nitems, T, max_iters=1)

  obs_data_row, _ = to_mat(np.vstack([train_data, valid_data]), nusers, nitems)
  test_data_row, _ = to_mat(test_data, nusers, nitems)

  terr = m.mse_err(test_data)
  #tprec, ntprec, num_users = m.prec_err(test_data_row, obs_data_row, T=T)
  tprec, ntprec, num_users = m.prec_err(test_data_row, obs_data_row, full=True, T=T, output_ranking=True)
  #tmar, num_users = m.mar_err(test_data_row, obs_data_row, full=True)
  tmrr, num_users = m.mrr_err(test_data_row, obs_data_row, full=True)
  logger.info('test err: %f, test mrr (%d users): %f\n' % (terr, num_users, tmrr))

  if not test_only and save_model:
    logger.info('saving model')
    train_data_row, train_data_col = to_mat(np.vstack([train_data, valid_data]), nusers, nitems)
    m.save(train_data_row, train_data_col)

  dic = {'mse' : terr, 'p@%d' % T : tprec, 'normalized_p@%d' % T: ntprec, 'mrr' : tmrr }
  #dic = {'mse' : terr, 'var' : tmar, 'mrr' : tmrr }

  return dic



def solve_reg_least_squares_par(d, U, V, a, b, lambda_):

  #num_cores = multiprocessing.cpu_count()

  a_m_b = a-b
  nz_items = np.array(d.sum(axis=0).nonzero()[1]).flatten()
  bVV = b * np.dot(V[nz_items,:].T,V[nz_items,:]) + lambda_ * np.eye(U.shape[1])

  #def processInput(i):
  #results = Parallel(n_jobs=num_cores)(delayed(processInput)(i) for i in inputs)
  U = Parallel(n_jobs=5)(delayed(solve_reg_least_squares_oneuser)(d[u,:], U[u,:], V, bVV, a_m_b, a) for u in xrange(U.shape[0]))

  #set_trace()

  return U

def solve_reg_least_squares_oneuser(R, U, V, bVV, a_m_b, a):
  #nnz_idx = R!=0
  nnz_idx = np.array(R.nonzero()[1]).flatten()
  if(len(nnz_idx) == 0): # does user/item have ratings
    return U

  #self._U[u,:] = np.dot(np.linalg.inv(np.dot(np.dot(self._V.T, Cdiag), self._V) + np.eye(self._k)*self._u_vprior), \
  #               (np.dot(np.dot(self._V.T, Cdiag), R)))

  A = bVV + a_m_b * np.dot(V[nnz_idx,:].T, V[nnz_idx,:])
  b = a * V[nnz_idx,:].sum(axis=0)
  U = np.linalg.solve(A,b.T)

  return U


def solve_reg_least_squares(d, U, V, a, b, lambda_, nneg=False):
  a_m_b = a-b

  nz_items = np.array(d.sum(axis=0).nonzero()[1]).flatten()
  bVV = b * np.dot(V[nz_items,:].T,V[nz_items,:]) + lambda_ * np.eye(U.shape[1])

  for u in xrange(U.shape[0]):
    R = d[u,:]
    #nnz_idx = R!=0
    nnz_idx = np.array(R.nonzero()[1]).flatten()
    if(len(nnz_idx) == 0): # does user/item have ratings
      continue

    #self._U[u,:] = np.dot(np.linalg.inv(np.dot(np.dot(self._V.T, Cdiag), self._V) + np.eye(self._k)*self._u_vprior), \
    #               (np.dot(np.dot(self._V.T, Cdiag), R)))

    A = bVV + a_m_b * np.dot(V[nnz_idx,:].T, V[nnz_idx,:])
    bvec = a * V[nnz_idx,:].sum(axis=0)

    if nneg:
      U[u,:],_ = sco.nnls(A, bvec.T)
      U[u,:]  += np.random.rand(U.shape[1]) * 0.01 # add a bit of noise in case everything is 0
    else:
      U[u,:] = np.linalg.solve(A,bvec.T)

  return U


class Model:

  def __init__(self, n, m, k=50, a=1, b=0.01, u_vprior=0.1, v_vprior=0.1, experiment_dir='.', nneg=False, idx0_user=False, idx0_item=False):

    self._n = n
    self._m = m
    self._k = k

    self._a = a
    self._b = b
    self._a_m_b = self._a - self._b

    self._nneg = nneg

    self._U = np.random.rand(self._n,self._k)*0.01
    self._V = np.random.rand(self._m,self._k)*0.01
    #if self._nneg:
      # make factors non-negative
      #self._U -= np.min(self._U)
      #self._V -= np.min(self._V)

    self._u_vprior = u_vprior
    self._v_vprior = v_vprior

    self._experiment_dir = experiment_dir

    self._idx0_user = 0
    self._idx0_item = 0
    if idx0_user:
      self._idx0_user = 1
    if idx0_item:
      self._idx0_item = 1

    if self._nneg:
      logger.info('\t+ non-negative factors')
    logger.info('+ model created')

  def load(self, U, V):
    self._U = U
    self._V = V

  def save(self, obs_mat_row, obs_mat_col):
    #arr = np.arange(self._n)[:,np.newaxis]
    #np.savetxt(os.path.join(self._experiment_dir,'U.tsv'), np.hstack([arr, arr, self._U]), '%.8f', delimiter='\t')
    #arr = np.arange(self._m)[:,np.newaxis]
    #np.savetxt(os.path.join(self._experiment_dir,'V.tsv'), np.hstack([arr, arr, self._V]), '%.8f', delimiter='\t')

    np.savetxt(os.path.join(self._experiment_dir,'U.tsv'), self._U, '%.8f', delimiter='\t')
    np.savetxt(os.path.join(self._experiment_dir,'V.tsv'), self._V, '%.8f', delimiter='\t')

    # only write-out users/items with ratings in train (makes it easier to load into PF code)
    nz_users = np.array(obs_mat_row.sum(axis=1).nonzero()[0]).flatten()
    np.savetxt(os.path.join(self._experiment_dir,'U_gaprec.tsv'), np.hstack([nz_users[:,np.newaxis], nz_users[:,np.newaxis]+self._idx0_user, self._U[nz_users,:]]), '%.8f', delimiter='\t')
    nz_items = np.array(obs_mat_col.sum(axis=0).nonzero()[1]).flatten()
    np.savetxt(os.path.join(self._experiment_dir,'V_gaprec.tsv'), np.hstack([nz_items[:,np.newaxis], nz_items[:,np.newaxis]+self._idx0_item, self._V[nz_items,:]]), '%.8f', delimiter='\t')

    if not self._nneg:
      minimum = min(np.min(self._U), np.min(self._V))
      if minimum > 0:
        minimum = 0
      np.savetxt(os.path.join(self._experiment_dir,'U_pos.tsv'), self._U-minimum, '%.8f', delimiter='\t')
      np.savetxt(os.path.join(self._experiment_dir,'V_pos.tsv'), self._V-minimum, '%.8f', delimiter='\t')

  def predict_pair(self, user, item):
    return np.dot(self._U[user,:], self._V[item,:].T)

  def predict_user(self, user, max_items = None):
    """
      Return an array of prediction for each item according to the user provided.
      If max_items is provided, return an array of top <max_items> predicted for the input user.
    """

    if max_items is None:
      return np.dot(self._U[user,:], self._V.T)
    else:
      result = np.dot(self._U[user,:], self._V.T)
      return np.argsort(result)[-max_items:]

  def predict_all(self):
    if not preds_up_to_date:
      self._preds = np.dot(self._U, self._V.T)
    return self._preds

  def mrr_err(self, test_mat, obs_mat, full=False):
    mrr = 0

    fraction = 0.1
    if not full:
      users = np.random.permutation(min(int(test_mat.shape[0]*fraction),200))
    else:
      #users = xrange(test_mat.shape[0])
      users = np.random.permutation(min(int(test_mat.shape[0]*fraction),1000))

    rr = 0
    user_wo_ratings = 0
    for u in users:
      test_idx = np.nonzero(test_mat[u,:])[1]
      if len(test_idx) == 0:
        user_wo_ratings += 1
        continue

      preds = self.predict_user(u)
      preds = preds.T #!!!
      preds[np.array(obs_mat[u,:].nonzero()[1]).flatten()] = -np.inf # remove train

      rr += (1. / (np.argsort(np.argsort(-preds))[test_idx] + 1)).sum()
    mrr = rr / (len(users) - user_wo_ratings) if len(users) != user_wo_ratings else 1.0

    return mrr, len(users)-user_wo_ratings


  def mar_err(self, test_mat, obs_mat, full=False):
    mar = 0

    fraction = 0.1
    if not full:
      users = np.random.permutation(min(int(test_mat.shape[0]*fraction),200))
    else:
      #users = xrange(test_mat.shape[0])
      users = np.random.permutation(min(int(test_mat.shape[0]*fraction),1000))

    ar = 0
    user_wo_ratings = 0
    for u in users:
      test_idx = np.nonzero(test_mat[u,:])[1]
      if len(test_idx) == 0:
        user_wo_ratings += 1
        continue

      preds = self.predict_user(u)
      preds[np.array(obs_mat[u,:].nonzero()[1]).flatten()] = -np.inf # remove train

      ar += np.mean(np.argsort(np.argsort(-preds))[test_idx])
    mar = ar / (len(users) - user_wo_ratings)

    return mar, len(users)-user_wo_ratings


  def prec_err(self, test_mat, obs_mat, full=False, T=100, output_ranking=False):
    precision = 0
    normalized_precision = 0
    user_wo_ratings = 0

    fraction = 0.1
    if not full:
      users = np.random.permutation(min(int(test_mat.shape[0]*fraction),200))
    else:
      #users = xrange(test_mat.shape[0])
      users = np.random.permutation(min(int(test_mat.shape[0]*fraction),1000))

    if output_ranking:
       f = open(os.path.join(self._experiment_dir,'ranking.tsv'),'w')
    for u in users:
      nnz_idx = np.nonzero(test_mat[u,:])[1]
      if len(nnz_idx) == 0:
        user_wo_ratings += 1
        continue

      preds = self.predict_user(u)
      preds[np.array(obs_mat[u,:].nonzero()[1]).flatten()] = -np.inf # remove train
      #preds = test_mat[u,:].toarray().flatten()
      #idx = set(preds.argsort()[-T:])
      idx = set(np.argpartition(-preds,T)[:T])
      #if idx_ != idx:
      #  logger.info(len(idx), len(idx_))
      #  set_trace()
      num_inter = len(idx.intersection(nnz_idx))
      normalized_precision += num_inter/float(min(T, nnz_idx.size))
      precision += num_inter/float(T)

      if output_ranking:
          for j in list(preds.argsort()[-T:]):
            f.write('%d\t%d\t%f\t%d\n' % (u+self._idx0_user, j+self._idx0_item, preds[j], test_mat[u,j]))

    if output_ranking:
      f.close()

    return precision/(len(users)-user_wo_ratings), normalized_precision/(len(users)-user_wo_ratings), len(users)-user_wo_ratings



  def mse_err(self, data):
    preds = map(lambda i: self.predict_pair(data[i,0], data[i,1]), xrange(data.shape[0]))
    error = ((preds - data[:,2])**2).sum()

    return error/data.shape[0]

  def update_u(self, data_mat):
    self._U = solve_reg_least_squares(data_mat, self._U, self._V, self._a, self._b, self._u_vprior, nneg=self._nneg)

  def update_v(self, data_mat):
    self._V = solve_reg_least_squares(data_mat.T, self._V, self._U, self._a, self._b, self._v_vprior, nneg=self._nneg)

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='GMF')
  parser.add_argument('--dir', type=str, required=True, help='location data directory')
  parser.add_argument('--dat_name', type=str, required=True, help='name of dataset')
  parser.add_argument('-k', type=int, required=True, help='size of latent representations')
  parser.add_argument('--nitems', type=int, required=False, default = 0, help='number of items')
  parser.add_argument('--nusers', type=int, required=False, default = 0, help='number of users')
  parser.add_argument('--lambda_u', type=float, required=True, help='u regularizer')
  parser.add_argument('--lambda_v', type=float, required=True, help='v regularizer')
  parser.add_argument('--nneg', action='store_true', help='force the latent factors to have non-negative means')
  parser.add_argument('--load', type=str, required=False, help='directory to load U/V from')
  args = parser.parse_args()

  nusers, nitems, train, valid, test, idx0_user, idx0_item = load_data(args.dir)
  # nitems = 599621
  if args.nitems != 0:
    nitems = args.nitems

  if args.nusers != 0:
    nusers = args.nusers

  eval_dir = '%s-nusers%d-mitems%d-k%d-lu%s-lu%s' % (args.dat_name, nusers, nitems, args.k, str(args.lambda_u).rstrip('0'), str(args.lambda_v).rstrip('0'))
  if args.nneg:
    eval_dir += '-nneg'

  if not os.path.exists(eval_dir):
    os.mkdir(eval_dir)
    logger.info('+ creating eval dir: %s', eval_dir)
  else:
    logger.info('+ using eval dir: %s', eval_dir)

  b = float(train.shape[0]) / (nusers * nitems)
  logger.info('+ b: %s', b)

  model = Model(nusers, nitems, b=b, k=args.k, u_vprior=args.lambda_u, v_vprior=args.lambda_v, experiment_dir=eval_dir,nneg=args.nneg,idx0_user=idx0_user, idx0_item=idx0_item)
  if args.load is None:
    errs = run(model, train, valid, test, nusers, nitems, 100)
  else:
    U = np.loadtxt(os.path.join(args.load, 'U.tsv'))
    V = np.loadtxt(os.path.join(args.load, 'V.tsv'))

    U = to_mat(U, nusers, args.k)[0].toarray()
    V = to_mat(V, nitems, args.k)[0].toarray()

    # set_trace()
    if U.shape[1] != args.k:
      U = U[:,-args.k:]
      logger.info('resizing U to %s', U.shape)
    if V.shape[1] != args.k:
      V = V[:,-args.k:]
      logger.info('resizing V to %s', V.shape)
    model.load(U,V)
    logger.info('+ U&V loaded')
    errs = run(model, train, valid, test, nusers, nitems, 100, test_only=True)

  logger.info("Finished running...")

  if not os.path.exists('results.txt'):
    with open('results.txt', 'w') as f:
      f.write('Dataset\tEvaluation directory\tEval metrics\n')
      f.write('============================================\n')

  with open('results.txt', 'a') as f:
    f.write(args.dat_name + '\t')
    f.write(eval_dir + '\t')
    for err_name,err in errs.iteritems():
      f.write('%s:%f\t' % (err_name, err))
    f.write('\n')