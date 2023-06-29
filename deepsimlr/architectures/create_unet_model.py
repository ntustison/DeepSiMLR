import torch
import torch.nn as nn

class create_unet_model_2d(nn.Module):
    def __init__(self, input_number_of_channels,
                       number_of_outputs=2,
                       number_of_layers=4,
                       number_of_filters_at_base_layer=32,
                       number_of_filters=None,
                       convolution_kernel_size=(3, 3),
                       deconvolution_kernel_size=(2, 2),
                       pool_size=(2, 2),
                       strides=(2, 2),
                       mode='classification',
                       additional_options=None
                      ):

        super(create_unet_model_2d, self).__init__()

        def nn_unet_activation_2d(number_of_features):
            x = nn.Sequential(nn.InstanceNorm2d(number_of_features), nn.LeakyReLU(0.01))
            return x

        initial_convolution_kernel_size = convolution_kernel_size
        add_attention_gating = False
        nn_unet_activation_style = False

        if additional_options is not None:

            if "attentionGating" in additional_options:
                add_attention_gating = True

            if "nnUnetActivationStyle" in additional_options:
                nn_unet_activation_style = True

            option = [o for o in additional_options if o.startswith('initialConvolutionKernelSize')]
            if not not option:
                initial_convolution_kernel_size = option[0].replace("initialConvolutionKernelSize", "")
                initial_convolution_kernel_size = initial_convolution_kernel_size.replace("[", "")
                initial_convolution_kernel_size = int(initial_convolution_kernel_size.replace("]", ""))

        # Specify the number of filters

        number_of_layers = number_of_layers

        if number_of_filters is not None:
            number_of_layers = len(number_of_filters)
        else:
            number_of_filters = list()
            for i in range(number_of_layers):
                number_of_filters.append(number_of_filters_at_base_layer * 2**i)
        print(number_of_filters)

        # Encoding path

        self.pool = nn.MaxPool2d(kernel_size=pool_size, stride=strides)

        self.encoding_convolution_layers = nn.ModuleList()
        for i in range(number_of_layers):

            print("i = " + str(i))

            conv1 = None
            if i == 0:
                conv1 = nn.Conv2d(in_channels=input_number_of_channels,
                                  out_channels=number_of_filters[i],
                                  kernel_size=initial_convolution_kernel_size,
                                  padding='same')
            else:
                conv1 = nn.Conv2d(in_channels=number_of_filters[i-1],
                                  out_channels=number_of_filters[i],
                                  kernel_size=convolution_kernel_size,
                                  padding='same')

            conv2 = None
            if i == 0:
                conv2 = nn.Conv2d(in_channels=number_of_filters[i],
                                  out_channels=number_of_filters[i],
                                  kernel_size=initial_convolution_kernel_size,
                                  padding='same')
            else:
                conv2 = nn.Conv2d(in_channels=number_of_filters[i],
                                  out_channels=number_of_filters[i],
                                  kernel_size=convolution_kernel_size,
                                  padding='same')

            if nn_unet_activation_style:
                self.encoding_convolution_layers.append(nn.Sequential(conv1, nn_unet_activation_2d(number_of_filters[i]),
                                                                      conv2, nn_unet_activation_2d(number_of_filters[i])))
            else:
                self.encoding_convolution_layers.append(nn.Sequential(conv1, nn.ReLU(), conv2, nn.ReLU()))

        # Decoding path

        self.upsample = nn.Upsample(scale_factor=pool_size)

        self.decoding_convolution_transpose_layers = nn.ModuleList()
        self.decoding_convolution_layers = nn.ModuleList()
        for i in range(1, number_of_layers):
            deconv = nn.ConvTranspose2d(in_channels=number_of_filters[number_of_layers-i],
                                        out_channels=number_of_filters[number_of_layers-i-1],
                                        kernel_size=deconvolution_kernel_size,
                                        padding=0)
            if nn_unet_activation_style:
                self.decoding_convolution_transpose_layers.append(
                    nn.Sequential(deconv, nn_unet_activation_2d(number_of_filters[number_of_layers-i-1])))
            else:
                self.decoding_convolution_transpose_layers.append(deconv)

            conv = nn.Conv2d(in_channels=number_of_filters[number_of_layers-i-1],
                             out_channels=number_of_filters[number_of_layers-i-1],
                             kernel_size=deconvolution_kernel_size,
                             padding="same")

            if nn_unet_activation_style:
                self.decoding_convolution_layers.append(nn.Sequential(conv, nn_unet_activation_2d(number_of_filters[number_of_layers-i-1]),
                                                                      conv, nn_unet_activation_2d(number_of_filters[number_of_layers-i-1])))
            else:
                self.decoding_convolution_layers.append(nn.Sequential(conv, nn.ReLU(), conv, nn.ReLU()))

        conv = nn.Conv2d(in_channels=number_of_filters[0],
                         out_channels=number_of_outputs,
                         kernel_size=1,
                         padding='same')

        if mode == 'sigmoid':
            self.output = nn.Sequential(conv, nn.Sigmoid())
        elif mode == 'classification':
            self.output = nn.Sequential(conv, nn.Softmax(dim=1))
        elif mode == 'regression':
            self.output = nn.Sequential(conv, nn.Linear())
        else:
            raise ValueError('mode must be either `classification`, `regression` or `sigmoid`.')

    def forward(self, x):

        # Encoding path

        number_of_layers = len(self.encoding_convolution_layers)

        encoding_path = x
        encoding_tensor_layers = list()
        for i in range(number_of_layers):
            print("i = " + str(i))
            encoding_path = self.encoding_convolution_layers[i](encoding_path)
            print(encoding_path.size())
            encoding_path = self.pool(encoding_path)
            print(encoding_path.size())
            encoding_tensor_layers.append(encoding_path)

        # Decoding path
        output = encoding_path
        for i in range(1, number_of_layers):
            print("ii = " + str(i))
            print(output.size())
            output = self.decoding_convolution_transpose_layers[i-1](output, output.size())
            print(output.size())
            output = self.upsample(output)
            print(output.size())
            output = torch.cat([output, encoding_tensor_layers[number_of_layers-i-1]], 1)
            output = self.decoding_convolution_layers[i-1](output)

        output = self.output(output)

        return output
