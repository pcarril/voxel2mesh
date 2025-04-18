 
import os
GPU_index = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = GPU_index

  
import logging
import torch
import numpy as np
from train import Trainer
from evaluate import Evaluator  



from shutil import copytree, ignore_patterns
import torch.optim as optim
from torch.utils.data import DataLoader
from utils.utils_common import DataModes

import wandb

from IPython import embed 
from utils.utils_common import mkdir

from config import load_config
from model.voxel2mesh import Voxel2Mesh as network



logger = logging.getLogger(__name__)

 
def init(cfg):

    save_path = cfg.save_path + cfg.save_dir_prefix + str(cfg.experiment_idx).zfill(3)
    
    mkdir(save_path) 
 
    trial_id = (len([dir for dir in os.listdir(save_path) if 'trial' in dir]) + 1) if cfg.trial_id is None else cfg.trial_id
    trial_save_path = save_path + '/trial_' + str(trial_id) 

    if not os.path.isdir(trial_save_path):
        mkdir(trial_save_path) 
        copytree(os.getcwd(), trial_save_path + '/source_code', ignore=ignore_patterns('*.git','*.txt','*.tif', '*.pkl', '*.off', '*.so', '*.json','*.jsonl','*.log','*.patch','*.yaml','wandb','run-*'))

  
    seed = trial_id
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.enabled = True  # speeds up the computation 

    return trial_save_path, trial_id

def main():

    exp_id = 3

    # Initialize
    cfg = load_config(exp_id)
    trial_path, trial_id = init(cfg) 
 
    print('Experiment ID: {}, Trial ID: {}'.format(cfg.experiment_idx, trial_id))

    print("Create network")
    classifier = network(cfg)
    classifier.cuda()

    wandb.init(name='Experiment_{}/trial_{}'.format(cfg.experiment_idx, trial_id), project="vm-net", dir=trial_path)
 
    print("Initialize optimizer")
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, classifier.parameters()), lr=cfg.learning_rate)  
  
    print("Load pre-processed data") 
    data_obj = cfg.data_obj 
    data = data_obj.quick_load_data(cfg, trial_id)

    loader = DataLoader(data[DataModes.TRAINING], batch_size=classifier.config.batch_size, shuffle=True)
  
    print("Trainset length: {}".format(loader.__len__()))

    print("Initialize evaluator")
    evaluator = Evaluator(classifier, optimizer, data, trial_path, cfg, data_obj)


    print("Initialize trainer")
    trainer = Trainer(classifier, loader, optimizer, cfg.numb_of_itrs, cfg.eval_every, trial_path, evaluator)

    if cfg.trial_id is not None:
        print("Loading pretrained network")
        trial_path = 'C:\\Users\pcarril\\PycharmProjects\\voxel2mesh_LV_003\\trial_1'
        save_path = trial_path + '/best_performance3/model.pth'
        checkpoint = torch.load(save_path)
        classifier.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        epoch = checkpoint['epoch']
    else:
        epoch = 0

    trainer.train(start_iteration=epoch)

    # To evaluate a pretrained model, uncomment line below and comment the line above
    # evaluator.evaluate(epoch)

if __name__ == "__main__": 
    main()