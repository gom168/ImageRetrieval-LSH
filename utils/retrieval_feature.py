# coding=utf-8
# /usr/bin/env pythpn

'''
Author: yinhao
Email: yinhao_x@163.com
Wechat: xss_yinhao
Github: http://github.com/yinhaoxs
data: 2019-11-23 18:26
desc:
'''

import os
from PIL import Image
from lshash.lshash import LSHash
import torch
from torchvision import transforms
from cirtorch.networks.imageretrievalnet import init_network, extract_vectors

# setting up the visible GPU
os.environ['CUDA_VISIBLE_DEVICES'] = "0"


class ImageProcess():
    def __init__(self, img_dir):
        self.img_dir = img_dir

    def process(self):
        imgs = list()
        for root, dirs, files in os.walk(self.img_dir):
            for file in files:
                img_path = os.path.join(root + os.sep, file)
                try:
                    image = Image.open(img_path)
                    if max(image.size) / min(image.size) < 5:
                        imgs.append(img_path)
                    else:
                        continue
                except:
                    print("image height/width ratio is small")

        return imgs


class AntiFraudFeatureDataset():
    def __init__(self, img_dir, network, feature_path='', index_path=''):
        self.img_dir = img_dir
        self.network = network
        self.feature_path = feature_path
        self.index_path = index_path

    def constructfeature(self, hash_size, input_dim, num_hashtables):
        multiscale = '[1]'
        print(">> Loading network:\n>>>> '{}'".format(self.network))
        # state = load_url(PRETRAINED[args.network], model_dir=os.path.join(get_data_root(), 'networks'))
        state = torch.load(self.network)
        # parsing net params from meta
        # architecture, pooling, mean, std required
        # the rest has default values, in case that is doesnt exist
        net_params = {}
        net_params['architecture'] = state['meta']['architecture']
        net_params['pooling'] = state['meta']['pooling']
        net_params['local_whitening'] = state['meta'].get('local_whitening', False)
        net_params['regional'] = state['meta'].get('regional', False)
        net_params['whitening'] = state['meta'].get('whitening', False)
        net_params['mean'] = state['meta']['mean']
        net_params['std'] = state['meta']['std']
        net_params['pretrained'] = False
        # network initialization
        net = init_network(net_params)
        net.load_state_dict(state['state_dict'])
        print(">>>> loaded network: ")
        print(net.meta_repr())
        # setting up the multi-scale parameters
        ms = list(eval(multiscale))
        print(">>>> Evaluating scales: {}".format(ms))
        # moving network to gpu and eval mode
        if torch.cuda.is_available():
            net.cuda()
        net.eval()

        # set up the transform
        normalize = transforms.Normalize(
            mean=net.meta['mean'],
            std=net.meta['std']
        )
        transform = transforms.Compose([
            transforms.ToTensor(),
            normalize
        ])

        # extract database and query vectors
        print('>> database images...')
        images = ImageProcess(self.img_dir).process()
        vecs, img_paths = extract_vectors(net, images, 1024, transform, ms=ms)
        img_paths_tep = [str(p) for p in img_paths]
        feature_dict = dict(zip(img_paths_tep, list(vecs.detach().cpu().numpy().T)))
        # index
        lsh = LSHash(hash_size=int(hash_size), input_dim=int(input_dim), num_hashtables=int(num_hashtables))
        for img_path, vec in feature_dict.items():
            lsh.index(vec.flatten(), extra_data=img_path)

        # ## 保存索引模型
        # with open(self.feature_path, "wb") as f:
        #     pickle.dump(feature_dict, f)
        # with open(self.index_path, "wb") as f:
        #     pickle.dump(lsh, f)

        print("extract feature is done")
        return feature_dict, lsh

    def test_feature(self):
        multiscale = '[1]'
        print(">> Loading network:\n>>>> '{}'".format(self.network))
        # state = load_url(PRETRAINED[args.network], model_dir=os.path.join(get_data_root(), 'networks'))
        state = torch.load(self.network)
        # parsing net params from meta
        # architecture, pooling, mean, std required
        # the rest has default values, in case that is doesnt exist
        net_params = {}
        net_params['architecture'] = state['meta']['architecture']
        net_params['pooling'] = state['meta']['pooling']
        net_params['local_whitening'] = state['meta'].get('local_whitening', False)
        net_params['regional'] = state['meta'].get('regional', False)
        net_params['whitening'] = state['meta'].get('whitening', False)
        net_params['mean'] = state['meta']['mean']
        net_params['std'] = state['meta']['std']
        net_params['pretrained'] = False
        # network initialization
        net = init_network(net_params)
        net.load_state_dict(state['state_dict'])
        print(">>>> loaded network: ")
        print(net.meta_repr())
        # setting up the multi-scale parameters
        ms = list(eval(multiscale))
        print(">>>> Evaluating scales: {}".format(ms))
        # moving network to gpu and eval mode
        if torch.cuda.is_available():
            net.cuda()
        net.eval()

        # set up the transform
        normalize = transforms.Normalize(
            mean=net.meta['mean'],
            std=net.meta['std']
        )
        transform = transforms.Compose([
            transforms.ToTensor(),
            normalize
        ])

        # extract database and query vectors
        print('>> database images...')
        images = ImageProcess(self.img_dir).process()
        vecs, img_paths = extract_vectors(net, images, 1024, transform, ms=ms)
        img_paths_tep = [str(p) for p in img_paths]
        feature_dict = dict(zip(img_paths_tep, list(vecs.detach().cpu().numpy().T)))
        return feature_dict


if __name__ == '__main__':
    pass
