class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.weights_input_hidden = self.initialize_weights(input_size, hidden_size)
        self.weights_hidden_output = self.initialize_weights(hidden_size, output_size)

    def initialize_weights(self, input_size, output_size):
        import numpy as np
        return np.random.randn(input_size, output_size) * 0.01

    def forward(self, X):
        self.hidden_layer_activation = np.dot(X, self.weights_input_hidden)
        self.hidden_layer_output = self.sigmoid(self.hidden_layer_activation)
        self.output_layer_activation = np.dot(self.hidden_layer_output, self.weights_hidden_output)
        return self.sigmoid(self.output_layer_activation)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def train(self, X, y, learning_rate=0.01, epochs=1000):
        for epoch in range(epochs):
            output = self.forward(X)
            error = y - output
            self.backpropagate(X, error, learning_rate)

    def backpropagate(self, X, error, learning_rate):
        output_gradient = self.sigmoid_derivative(self.output_layer_activation)
        hidden_layer_error = error * output_gradient
        self.weights_hidden_output += np.dot(self.hidden_layer_output.T, hidden_layer_error) * learning_rate

        hidden_layer_gradient = self.sigmoid_derivative(self.hidden_layer_activation)
        hidden_layer_error = np.dot(hidden_layer_error, self.weights_hidden_output.T) * hidden_layer_gradient
        self.weights_input_hidden += np.dot(X.T, hidden_layer_error) * learning_rate

    def sigmoid_derivative(self, x):
        return x * (1 - x)