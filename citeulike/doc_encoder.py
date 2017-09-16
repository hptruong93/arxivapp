# -*- coding: utf-8 -*-

""" Auto Encoder Example.
Using an auto encoder on MNIST handwritten digits.
References:
    Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner. "Gradient-based
    learning applied to document recognition." Proceedings of the IEEE,
    86(11):2278-2324, November 1998.
Links:
    [MNIST Dataset] http://yann.lecun.com/exdb/mnist/
"""
from __future__ import division, print_function, absolute_import

import tensorflow as tf
import numpy as np
# import matplotlib.pyplot as plt

# Import MNIST data
# from tensorflow.examples.tutorials.mnist import input_data
# mnist = input_data.read_data_sets("MNIST_data", one_hot=True)


def _autoencode_paper(train_samples, validation_samples, to_encode_samples):
    assert train_samples.shape[1] == validation_samples.shape[1]

    print("Autoencoding: (training, validation) = ({}, {})".format(train_samples.shape[0], validation_samples.shape[0]))

    # Metadata about samples
    n_train = train_samples.shape[0]

    # Parameters
    learning_rate = 0.01
    training_epochs = np.inf #1000
    cost_threshold = 0.01
    batch_size = 256
    display_step = 20
    # examples_to_show = 10
    examples_to_show = validation_samples.shape[0]

    # Network Parameters
    n_hidden_1 = 1024 # 1st layer num features
    n_hidden_2 = 256 # 2nd layer num features
    # n_input = 784 # MNIST data input (img shape: 28*28)
    n_input = train_samples.shape[1]


    def get_train_batch(batch_index):
        return train_samples[batch_index * batch_size : (batch_index + 1) * batch_size,:]


    # tf Graph input (only pictures)
    X = tf.placeholder("float", [None, n_input])

    weights = {
        'encoder_h1': tf.Variable(tf.random_normal([n_input, n_hidden_1])),
        'encoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
        'decoder_h1': tf.Variable(tf.random_normal([n_hidden_2, n_hidden_1])),
        'decoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_input])),
    }
    biases = {
        'encoder_b1': tf.Variable(tf.random_normal([n_hidden_1])),
        'encoder_b2': tf.Variable(tf.random_normal([n_hidden_2])),
        'decoder_b1': tf.Variable(tf.random_normal([n_hidden_1])),
        'decoder_b2': tf.Variable(tf.random_normal([n_input])),
    }


    # Building the encoder
    def encoder(x):
        # Encoder Hidden layer with sigmoid activation #1
        layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['encoder_h1']),
                                       biases['encoder_b1']))
        # Decoder Hidden layer with sigmoid activation #2
        layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['encoder_h2']),
                                       biases['encoder_b2']))
        return layer_2


    # Building the decoder
    def decoder(x):
        # Encoder Hidden layer with sigmoid activation #1
        layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['decoder_h1']),
                                       biases['decoder_b1']))
        # Decoder Hidden layer with sigmoid activation #2
        layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['decoder_h2']),
                                       biases['decoder_b2']))
        return layer_2

    # Construct model
    encoder_op = encoder(X)
    decoder_op = decoder(encoder_op)

    # Prediction
    y_pred = decoder_op
    # Targets (Labels) are the input data.
    y_true = X

    # Define loss and optimizer, minimize the squared error
    cost = tf.reduce_mean(tf.pow(y_true - y_pred, 2))
    optimizer = tf.train.RMSPropOptimizer(learning_rate).minimize(cost)

    # Initializing the variables
    init = tf.global_variables_initializer()

    # Launch the graph
    with tf.Session() as sess:
        sess.run(init)
        total_batch = int(n_train/batch_size)
        # Training cycle
        # for epoch in range(training_epochs):
        epoch = -1
        previous_validation = 1
        while epoch < training_epochs:
            epoch += 1
            # Loop over all batches
            for i in range(total_batch):
                # batch_xs, batch_ys = mnist.train.next_batch(batch_size)
                batch_xs = get_train_batch(i)

                # Run optimization op (backprop) and cost op (to get loss value)
                _, c = sess.run([optimizer, cost], feed_dict={X: batch_xs})

            if c < cost_threshold:
                print("Epoch:", '%04d' % (epoch),
                      "cost=", "{:.9f}".format(c))
                break

            # Display logs per epoch step
            if epoch % display_step == 0:
                validation_cost = sess.run(cost, feed_dict={X: validation_samples[:examples_to_show]})
                print("Epoch:", '%04d' % (epoch),
                      "cost =", "{:.9f}".format(c),
                      "validation =", "{:.9f}".format(validation_cost))

                if validation_cost > previous_validation:
                    print("Terminating due to increase in validation cost.")
                    break
                else:
                    previous_validation = validation_cost

        print("Optimization Finished!")

        # Applying encode over validation set
        # print("Encoding validation vector {}".format(validation_samples[:examples_to_show].shape))

        step_size = 1000
        total_samples = to_encode_samples.shape[0]

        index = 0
        encodings = []
        costs = []
        while index <= total_samples:
            encoded_papers, run_cost = sess.run([encoder_op, cost], feed_dict={X: to_encode_samples[index : index + step_size]})
            encodings.append(encoded_papers)
            costs.append(run_cost)

            index += step_size

        encoded_papers = np.vstack(encodings)
        cost = np.average(costs)
        print("Encoded into {} with cost {}".format(encoded_papers.shape, cost))

        print("Done")
        return encoded_papers


def autoencode_paper(papers):
    n_samples = papers.shape[0]
    assert n_samples % 10 == 0

    n_train = int(n_samples * 0.9)
    n_validation = int(n_samples * 0.1)

    np.random.shuffle(papers)
    train_samples = papers[:n_train,:]
    validation_samples = papers[-n_validation:,:]

    return _autoencode_paper(train_samples, validation_samples, papers)