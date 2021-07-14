import torch
import torch.nn as nn

import math

class MultiHeadAttention(nn.Module):
    def __init__(self, hidden_size, num_of_attention_heads):
        super().__init__()
        assert (hidden_size % num_of_attention_heads) == 0, "The hidden size is not a multiple of the number of attention heads"

        self.num_attention_heads = num_of_attention_heads
        self.attention_head_size = int(hidden_size / num_of_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.query = nn.Linear(hidden_size, self.all_head_size, bias=False)
        self.key = nn.Linear(hidden_size, self.all_head_size, bias=False)
        self.value = nn.Linear(hidden_size, self.all_head_size, bias=False)
        self.dense = nn.Linear(hidden_size, hidden_size, bias=False)
        #self.query.weight.data = torch.eye(d_model)
        #self.key.weight.data = torch.eye(d_model)
        #self.value.weight.data = torch.eye(d_model)
        #self.dense.weight.data = torch.eye(d_model)
        nn.init.orthogonal_(self.query.weight)
        nn.init.orthogonal_(self.key.weight)
        nn.init.orthogonal_(self.value.weight)
        nn.init.orthogonal_(self.dense.weight)

    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(self, query, key, value):
        mixed_query_layer = self.query(query)  # [Batch_size x Seq_length x Hidden_size]
        mixed_key_layer = self.key(key)  # [Batch_size x Seq_length x Hidden_size]
        mixed_value_layer = self.value(value)  # [Batch_size x Seq_length x Hidden_size]

        query_layer = self.transpose_for_scores(
            mixed_query_layer)  # [Batch_size x Num_of_heads x Query_Seq_length x Head_size]
        key_layer = self.transpose_for_scores(mixed_key_layer)  # [Batch_size x Num_of_heads x Seq_length x Head_size]
        value_layer = self.transpose_for_scores(
            mixed_value_layer)  # [Batch_size x Num_of_heads x Seq_length x Head_size]

        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1,
                                                                         -2))  # [Batch_size x Num_of_heads x Query_Seq_length x Seq_length]
        attention_scores = attention_scores / math.sqrt(
            self.attention_head_size)  # [Batch_size x Num_of_heads x Query_Seq_length x Seq_length]
        attention_probs = nn.Softmax(dim=-1)(attention_scores)  # [Batch_size x Num_of_heads x Query_Seq_length x Seq_length]
        context_layer = torch.matmul(attention_probs,
                                     value_layer)  # [Batch_size x Num_of_heads x Query_Seq_length x Head_size]

        context_layer = context_layer.permute(0, 2, 1,
                                              3).contiguous()  # [Batch_size x Query_Seq_length x Num_of_heads x Head_size]
        new_context_layer_shape = context_layer.size()[:-2] + (
        self.all_head_size,)  # [Batch_size x Query_Seq_length x Hidden_size]
        context_layer = context_layer.view(*new_context_layer_shape)  # [Batch_size x Query_Seq_length x Hidden_size]

        output = self.dense(context_layer)

        return output

if __name__ == "__main__":
    num_of_attention_heads = 2
    hidden_size = 4

    selfattn = BertSelfAttention(hidden_size, num_of_attention_heads)
    print(selfattn)
    embed_rand = torch.rand((1, 3, 4))
    print(f"Embed Shape: {embed_rand.shape}")
    print(f"Embed Values:\n{embed_rand}")

    output = selfattn(embed_rand, embed_rand, embed_rand)
    print(f"Output Shape: {output.shape}")
    print(f"Output Values:\n{output}")