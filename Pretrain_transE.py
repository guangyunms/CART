# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 18:23:18 2020

@author: kvn646
"""

# BB-8 and R2-D2 are best friends.
CUDA_LAUNCH_BLOCKING="1"
import sys
sys.path.insert(0, '../FM')
sys.path.insert(0, '../yelp')

import pickle
import torch
import argparse

import time
import numpy as np
import json

from config import global_config as cfg
from epi import run_one_episode, update_PN_model
from pn import PolicyNetwork
import copy

from collections import defaultdict

import random
import os.path
import json
import math
import regex as re
import generate_data
import pn_init

#train_dict,valid_dict,test_dict = generate_data.get_data()
random.seed(1)

the_max = 0
for k, v in cfg.item_dict.items():
    if the_max < max(v['feature_index']):
        the_max = max(v['feature_index'])
print(the_max)
FEATURE_COUNT = the_max + 1

success_at_turn_list = [0] * 10


#def cuda_(var):
#    return var.cuda() if torch.cuda.is_available()else var


def main():
    parser = argparse.ArgumentParser(description="Run conversational recommendation.")
    parser.add_argument('-mt', type=int, dest='mt', help='MAX_TURN', default = 10)
    parser.add_argument('-playby', type=str, dest='playby', help='playby', default ='policy' )
    # options include:
    # AO: (Ask Only and recommend by probability)
    # RO: (Recommend Only)
    # policy: (action decided by our policy network)
    parser.add_argument('-fmCommand', type=str, dest='fmCommand', help='fmCommand', default =8)
    # the command used for FM, check out /EAR/lastfm/FM/
    parser.add_argument('-optim', type=str, dest='optim', help='optimizer', default ='SGD')
    # the optimizer for policy network
    parser.add_argument('-lr', type=float, dest='lr', help='lr', default =0.001)
    # learning rate of policy network
    parser.add_argument('-decay', type=float, dest='decay', help='decay', default =0)
    # weight decay
    parser.add_argument('-TopKTaxo', type=int, dest='TopKTaxo', help='TopKTaxo', default =3)
    # how many 2-layer feature will represent a big feature. Only Yelp dataset use this param, lastFM have no effect.
    parser.add_argument('-gamma', type=float, dest='gamma', help='gamma', default =0.7)
    # gamma of training policy network
    parser.add_argument('-trick', type=int, dest='trick', help='trick', default =0)
    # whether use normalization in training policy network
    parser.add_argument('-startFrom', type=int, dest='startFrom', help='startFrom', default =0)
    # startFrom which user-item interaction pair
    parser.add_argument('-endAt', type=int, dest='endAt', help='endAt', default =3241) #train: 783 valid： 235
    # endAt which user-item interaction pair
    parser.add_argument('-strategy', type=str, dest='strategy', help='strategy', default ='maxsim')
    # strategy to choose question to ask, only have effect
    parser.add_argument('-eval', type=int, dest='eval', help='eval', default =0)
    # whether current run is for evaluation
    parser.add_argument('-mini', type=int, dest='mini', help='mini', default =1)
    # means `mini`-batch update the FM
    parser.add_argument('-alwaysupdate', type=int, dest='alwaysupdate', help='alwaysupdate', default =1)
    # means always mini-batch update the FM, alternative is that only do the update for 1 time in a session.
    # we leave this exploration tof follower of our work.
    parser.add_argument('-initeval', type=int, dest='initeval', help='initeval', default =0)
    # whether do the evaluation for the `init`ial version of policy network (directly after pre-train)
    parser.add_argument('-upoptim', type=str, dest='upoptim', help='upoptim', default ='SGD')
    # optimizer for reflection stafe
    parser.add_argument('-upcount', type=int, dest='upcount', help='upcount', default =1)
    # how many times to do reflection
    parser.add_argument('-upreg', type=float, dest='upreg', help='upreg', default =0.001)
    # regularization term in
    parser.add_argument('-code', type=str, dest='code', help='code', default ='stable')
    # We use it to give each run a unique identifier.
    parser.add_argument('-purpose', type=str, dest='purpose', help='purpose', default ='pretrain' )
    # options: pretrain, others
    parser.add_argument('-mod', type=str, dest='mod', help='mod', default ='ours')
    # options: CRM, EAR
    parser.add_argument('-mask', type=int, dest='mask', help='mask', default =0)
    # use for ablation study, 1, 2, 3, 4 represent our four segments, {ent, sim, his, len}

    A = parser.parse_args()

    # Note:
    # purpose = fmdata, playby: AOO, AOO_valid, are for sample training data and validation data.

    cfg.change_param(playby=A.playby, eval=A.eval, update_count=A.upcount, update_reg=A.upreg,
                     purpose=A.purpose, mod=A.mod, mask=A.mask)
    device = torch.device('cuda:1')
    random.seed(1)
#    random.shuffle(cfg.valid_list)
#    random.shuffle(cfg.test_list)
# ear data format: user_id item_id location_id
    the_valid_list_item = copy.copy(cfg.valid_list_item)
    the_valid_list_features = copy.copy(cfg.valid_list_features)
    
    the_test_list_item = copy.copy(cfg.test_list_item)
    the_test_list_features = copy.copy(cfg.test_list_features)
    
    the_train_list_item = copy.copy(cfg.train_list_item)
    the_train_list_features = copy.copy(cfg.train_list_features)
    
    print('length of train file is: ', len(the_valid_list_features))
#    random.shuffle(the_valid_list)
#    random.shuffle(the_test_list)

    # we random shuffle and split the valid and test set, for Action Stage training and evaluation respectively, to avoid the bias in the dataset.
#    all_list = cfg.valid_list + cfg.test_list
#    print('The length of all list is: {}'.format(len(all_list)))
#    random.shuffle(all_list)
#    the_valid_list = all_list[: int(len(all_list) / 2.0)]
#    the_test_list = all_list[int(len(all_list) / 2.0): ]

    gamma = A.gamma
#    FM_model = cfg.FM_model
    transE_model = cfg.transE_model
    if A.eval == 1:
#        if A.mod == 'ear':
#            fp = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-ear/PN-model-ear.txt'
#        if A.mod == 'crm':
#            fp = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-crm/PN-model-crm.txt'
        if A.mod == 'ours':
            fp = './data-ms/PN-model-ours/PN-model-ours.txt'
        if A.initeval == 1:
#            if A.mod == 'ear':
#                fp = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-ear/pretrain-model.pt'
#            if A.mod == 'crm':
#                fp = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-crm/pretrain-model.pt'
            if A.mod == 'ours':
                fp = './data-ms/PN-model-ours/pretrain-model.pt'
    else:
        # means training
#        if A.mod == 'ear':
#            fp = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-ear/pretrain-model.pt'
#        if A.mod == 'crm':
#            fp = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-crm/pretrain-model.pt'
        if A.mod == 'ours':
            fp = './data-ms/PN-model-ours/pretrain-model.pt'
            
    INPUT_DIM = 0
#    if A.mod == 'ear':
#        INPUT_DIM = 47 #12+12+15+8
#    if A.mod == 'crm':
#        INPUT_DIM = 289 #248+30+2+9
    if A.mod == 'ours':
        INPUT_DIM = 28 #11+10+8
#    print('fp is: {}'.format(fp))
    PN_model = PolicyNetwork(input_dim=INPUT_DIM, dim1=64, output_dim=12)
    start = time.time()

    try:
        PN_model.load_state_dict(torch.load(fp))
        print('Now Load PN pretrain from {}, takes {} seconds.'.format(fp, time.time() - start))
    except:
        print('Cannot load the model!!!!!!!!!\n fp is: {}'.format(fp))
        if cfg.play_by == 'policy':
            sys.exit()

    if A.optim == 'Adam':
        optimizer = torch.optim.Adam(PN_model.parameters(), lr=A.lr, weight_decay=A.decay)
    if A.optim == 'SGD':
        optimizer = torch.optim.SGD(PN_model.parameters(), lr=A.lr, weight_decay=A.decay)
    if A.optim == 'RMS':
        optimizer = torch.optim.RMSprop(PN_model.parameters(), lr=A.lr, weight_decay=A.decay)

    numpy_list = list()
    NUMPY_COUNT = 0

    sample_dict = defaultdict(list)
    conversation_length_list = list()
    
    # start episode
    for epi_count in range(A.startFrom, A.endAt):
        if epi_count % 1 == 0:
            print('------------------- It has processed {} episodes'.format(epi_count))
#        if epi_count >= len(cfg.item_dict):
#            continue
        start = time.time()

        # It is very important, to copy the model
        # Following for initialize FM model for each episode
        current_transE_model = copy.deepcopy(transE_model)
        current_transE_model.to(device)
        
        param1, param2 = list(), list()
        i = 0
        for name, param in current_transE_model.named_parameters():
            if i == 0 or i==1:
                param1.append(param)
                # param1: head, tail
            else:
                param2.append(param)
                # param2: time, category, cluster, type
            i += 1

        # following old code
        '''change to transE embedding'''
        optimizer1_transE, optimizer2_transE = None, None
        if A.purpose != 'fmdata':
            optimizer1_transE = torch.optim.Adagrad(param1, lr=0.01, weight_decay=A.decay)
            if A.upoptim == 'Ada':
                optimizer2_transE = torch.optim.Adagrad(param2, lr=0.01, weight_decay=A.decay)
            if A.upoptim == 'SGD':
                optimizer2_transE = torch.optim.SGD(param2, lr=0.001, weight_decay=A.decay)
        # end following

        if A.purpose != 'pretrain': #fmdata
            items = the_valid_list_item[epi_count]  #0 18 10 3 
            features = the_valid_list_features[epi_count] #3,21,2,1    21,12,2,1   22,7,2,1 
            item_list = items.strip().split(' ') 
            u = item_list[0] 
            item = item_list[-1]
            if A.eval == 1:
#                u, item, l = the_test_list_item[epi_count]
                items = the_test_list_item[epi_count]  #0 18 10 3 
                features = the_test_list_features[epi_count] #3,21,2,1    21,12,2,1   22,7,2,1 
                item_list = items.strip().split(' ') 
                u = item_list[0] 
                item = item_list[-1]          
                
            user_id = int(u)
            item_id = int(item)
        else:
            user_id = 0
            item_id = epi_count
            # it means that we accumulate FM training data, regardless which user. (c.f. our user simulator setting)

        if A.purpose == 'pretrain':
#            u, item = cfg.train_list[epi_count]
            items = the_train_list_item[epi_count]  #0 18 10 3 
            features = the_train_list_features[epi_count] #3,21,2,1    21,12,2,1   22,7,2,1 
            item_list = items.strip().split(' ') 
            u = item_list[0] 
            item = item_list[-1]
            user_id = int(u)
            item_id = int(item)
        print ("-----target item: ", item_id)
        big_feature_list = list()
        
        '''update L2.json'''
        for k, v in cfg.taxo_dict.items():
#            print (k,v)
            if len(set(v).intersection(set(cfg.item_dict[str(item_id)]['L2_Category_name']))) > 0:
#                print(user_id, item_id) #433,122
#                print (k)
                big_feature_list.append(k)
        
        write_fp = './data-ms/interaction-log/{}/v4-code-{}-s-{}-e-{}-lr-{}-gamma-{}-playby-{}-stra-{}-topK-{}-trick-{}-eval-{}-init-{}-mini-{}-always-{}-upcount-{}-upreg-{}-m-{}.txt'.format(
            A.mod.lower(), A.code, A.startFrom, A.endAt, A.lr, A.gamma, A.playby, A.strategy, A.TopKTaxo, A.trick,
            A.eval, A.initeval,
            A.mini, A.alwaysupdate, A.upcount, A.upreg, A.mask)
        
        '''care the sequence of facet pool items'''
        if cfg.item_dict[str(item_id)]['POI_Type'] is not None:
#            choose_pool = ['clusters', 'stars', 'POI_Type'] + big_feature_list 
            choose_pool = ['clusters', 'POI_Type'] + big_feature_list 
#            print (choose_pool)
#        else:
#            choose_pool = ['stars', 'city'] + big_feature_list

        choose_pool_original = choose_pool


        if A.purpose not in ['pretrain', 'fmdata']:
            # this means that: we are not collecting data for pretraining or fm data
            # then we only randomly choose one start attribute to ask!
            choose_pool = [random.choice(choose_pool)]

        # run the episode
#        print ('choose_pool: ', choose_pool)
        for c in choose_pool:
            start_facet = c
            with open(write_fp, 'a') as f:
                f.write(
                    'Starting new\nuser ID: {}, item ID: {} episode count: {}\n'.format(user_id, item_id, epi_count))
            if A.purpose != 'pretrain':
                log_prob_list, rewards, success, turn_count, known_feature_category = run_one_episode(current_transE_model, user_id, item_id, A.mt, False, write_fp,
                                                         A.strategy, A.TopKTaxo,
                                                         PN_model, gamma, A.trick, A.mini,
                                                         optimizer1_transE, optimizer2_transE, A.alwaysupdate, start_facet, A.mask, sample_dict, choose_pool_original,features, items)
            else:
                current_np = run_one_episode(current_transE_model, user_id, item_id, A.mt, False, write_fp,
                                                         A.strategy, A.TopKTaxo,
                                                         PN_model, gamma, A.trick, A.mini,
                                                         optimizer1_transE, optimizer2_transE, A.alwaysupdate, start_facet, A.mask, sample_dict, choose_pool_original,features, items)
                numpy_list += current_np
        # end run
        
        # check POI type, recommend location id by star, check the success. 
        # if match, success == true else false.
#        if A.purpose != 'pretrain':
#            if success == True:
#                if cfg.poi_dict[str(item_id)]['POI'] == 'Combined':
#                    max_location_star = max(cfg.poi_dict[str(item_id)]['stars'])
#                    index = cfg.poi_dict[str(item_id)]['stars'].index(max_location_star)
#                    location_id = cfg.poi_dict[str(item_id)]['Location_id'][index]
#                    if location_id == l:
#                        print('Combined Rec Success! in episode: {}.'.format(epi_count))
#                        success_at_turn_list[turn_count-1] += 1
#                    else:
#                        print('Combined Rec failed! in episode: {}.'.format(epi_count))
#
#                else:
#                    print('Independent Rec Success! in episode: {}.'.format(epi_count))
#                    success_at_turn_list[turn_count-1] += 1

        if A.purpose != 'pretrain':
            if success == True:
                print('Rec Success! in episode: {}.'.format(epi_count))
                success_at_turn_list[turn_count] += 1
        
        
        # update PN model
        if A.playby == 'policy' and A.eval != 1 and A.purpose != 'pretrain':
            update_PN_model(PN_model, log_prob_list, rewards, optimizer)
            print('updated PN model')
            current_length = len(log_prob_list)
            conversation_length_list.append(current_length)
        # end update
#        path1 = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-ours/trained_PN.pt'
#        torch.save(PN_model.state_dict(),path1)
#        path2 = 'C:/Users/kvn646/Desktop/MSAI-Project/final/CAL/basic/data/PN-model-ours/trained_PN.txt'
#        torch.save(PN_model.state_dict(),path2)

        check_span = 50
        if epi_count % check_span == 0 and epi_count >= 3 * check_span and cfg.eval != 1 and A.purpose != 'pretrain':
            # We use AT (average turn of conversation) as our stopping criterion
            # in training mode, save RL model periodically
            # save model first
            PATH = './data-ms/PN-model-{}/v4-code-{}-s-{}-e-{}-lr-{}-gamma-{}-playby-{}-stra-{}-topK-{}-trick-{}-eval-{}-init-{}-mini-{}-always-{}-upcount-{}-upreg-{}-m-{}-epi-{}.txt'.format(
                A.mod.lower(), A.code, A.startFrom, A.endAt, A.lr, A.gamma, A.playby, A.strategy, A.TopKTaxo, A.trick,
                A.eval, A.initeval,
                A.mini, A.alwaysupdate, A.upcount, A.upreg, A.mask, epi_count)
            torch.save(PN_model.state_dict(), PATH)
            print('Model saved at {}'.format(PATH))

            # a0 = conversation_length_list[epi_count - 4 * check_span: epi_count - 3 * check_span]
            a1 = conversation_length_list[epi_count - 3 * check_span: epi_count - 2 * check_span]
            a2 = conversation_length_list[epi_count - 2 * check_span: epi_count - 1 * check_span]
            a3 = conversation_length_list[epi_count - 1 * check_span: ]
            a1 = np.mean(np.array(a1))
            a2 = np.mean(np.array(a2))
            a3 = np.mean(np.array(a3))

            with open(write_fp, 'a') as f:
                f.write('$$$current turn: {}, a3: {}, a2: {}, a1: {}\n'.format(epi_count, a3, a2, a1))
            print('current turn: {}, a3: {}, a2: {}, a1: {}'.format(epi_count, a3, a2, a1))

            num_interval = int(epi_count / check_span)
            for i in range(num_interval):
                ave = np.mean(np.array(conversation_length_list[i * check_span: (i + 1) * check_span]))
                print('start: {}, end: {}, average: {}'.format(i * check_span, (i + 1) * check_span, ave))
                PATH = './data-ms/PN-model-{}/v4-code-{}-s-{}-e-{}-lr-{}-gamma-{}-playby-{}-stra-{}-topK-{}-trick-{}-eval-{}-init-{}-mini-{}-always-{}-upcount-{}-upreg-{}-m-{}-epi-{}.txt'.format(
                    A.mod.lower(), A.code, A.startFrom, A.endAt, A.lr, A.gamma, A.playby, A.strategy, A.TopKTaxo,
                    A.trick,
                    A.eval, A.initeval,
                    A.mini, A.alwaysupdate, A.upcount, A.upreg, A.mask, (i + 1) * check_span)
                print('Model saved at: {}'.format(PATH))

            if a3 > a1 and a3 > a2:
                print('Early stop of RL!')
                exit()

        # write control information
        if A.purpose != 'pretrain':
            with open(write_fp, 'a') as f:
                f.write('Big features are: {}\n'.format(choose_pool))
                if rewards is not None:
                    f.write('reward is: {}\n'.format(rewards.data.numpy().tolist()))
                f.write('WHOLE PROCESS TAKES: {} SECONDS\n'.format(time.time() - start))
        # end write

        # Write to pretrain numpy which is the pretrain data.
        if A.purpose == 'pretrain':
            if len(numpy_list) > 1000:
                with open('./data-ms/pretrain-numpy-data-{}/segment-{}-start-{}-end-{}.pk'.format(
                        A.mod, NUMPY_COUNT, A.startFrom, A.endAt), 'wb') as f:
                    pickle.dump(numpy_list, f)
                    print('Have written 1000 numpy arrays!')
                NUMPY_COUNT += 1
                numpy_list = list()
        # numpy_list is a list of list.
        # e.g. numpy_list[0][0]: int, indicating the action.
        # numpy_list[0][1]: a one-d array of length 81 for EAR, and 590 for CRM.
        # end write
    for i in range(len(success_at_turn_list)):
        success_rate = success_at_turn_list[i]/A.endAt
        print ('success rate is {} at turn {}'.format(success_rate, i+1))    
if __name__ == '__main__':
    main()
