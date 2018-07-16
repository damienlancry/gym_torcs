import tensorflow as tf
import tensorflow.contrib as tc
import tensorflow.contrib.layers as layers

class Model(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, obs, reuse=False):
        with tf.variable_scope(self.name) as scope:
            if reuse:
                scope.reuse_variables()

            x = obs
            convs = [(32,4,1),(32,4,1),(32,4,1)]
            for filters, kernel_size, stride in convs:
                fan_in = np.sqrt(np.prod(x.shape))
                x = tf.layers.conv2d(x,filters=filters,kernel_size=kernel_size,
                    strides=stride,
                    kernel_initializer=tf.random_uniform_initializer(minval=-1./fan_in, maxval=1./fan_in))
                if self.layer_norm:
                    x = tc.layers.layer_norm(x, center=True, scale=True)
                x = tf.nn.relu(x)

            x= tf.layers.flatten(x)
        return x


    @property
    def vars(self):
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name)

    @property
    def trainable_vars(self):
        return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.name)

    @property
    def perturbable_vars(self):
        return [var for var in self.trainable_vars if 'LayerNorm' not in var.name]


class Actor(Model):
    def __init__(self, nb_actions, name='actor', layer_norm=True):
        super(Actor, self).__init__(name=name)
        self.nb_actions = nb_actions
        self.layer_norm = layer_norm

    def __call__(self, obs, reuse=False):
        x = super(Actor, self).__call__(obs=obs,reuse=reuse)
        with tf.variable_scope(self.name) as scope:
            if reuse:
                scope.reuse_variables()

            hiddens = [200,200]
            for hidden in hiddens:
                fan_in = np.sqrt(np.prod(x.shape))
                x = tf.layers.dense(x, hidden,kernel_initializer=tf.random_uniform_initializer(minval=-1./fan_in, maxval=1./fan_in)))
                if self.layer_norm:
                    x = tc.layers.layer_norm(x, center=True, scale=True)
                x = tf.nn.relu(x)

            x = tf.layers.dense(x, self.nb_actions,
                kernel_initializer=tf.random_uniform_initializer(minval=-3e-4, maxval=3e-4))
            x = tf.nn.tanh(x)
        return x


class Critic(Model):
    def __init__(self, name='critic', layer_norm=True):
        super(Critic, self).__init__(name=name)
        self.layer_norm = layer_norm

    def __call__(self, obs, action, reuse=False):
        x = super(Actor, self).__call__(obs=obs,reuse=reuse)
        with tf.variable_scope(self.name) as scope:
            if reuse:
                scope.reuse_variables()

            fan_in = np.sqrt(np.prod(x.shape))
            x = tf.layers.dense(x,64,kernel_initializer=tf.random_uniform_initializer(minval=-1./fan_in, maxval=1./fan_in)))
            if self.layer_norm:
                x = tc.layers.layer_norm(x, center=True, scale=True)
            x = tf.nn.relu(x)

            fan_in = np.sqrt(np.prod(x.shape))
            x = tf.concat([x, action], axis=-1)
            x = tf.layers.dense(x, 64,kernel_initializer=tf.random_uniform_initializer(minval=-1./fan_in, maxval=1./fan_in)))
            if self.layer_norm:
                x = tc.layers.layer_norm(x, center=True, scale=True)
            x = tf.nn.relu(x)

            x = tf.layers.dense(x, 1, kernel_initializer=tf.random_uniform_initializer(minval=-3e-4, maxval=3e-4))
        return x


    @property
    def output_vars(self):
        output_vars = [var for var in self.trainable_vars if 'output' in var.name]
        return output_vars
