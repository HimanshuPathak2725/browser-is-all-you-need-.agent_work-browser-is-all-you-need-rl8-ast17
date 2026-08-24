# Implementing DNF-C03

Iter-19 trial 3 used `(score - 10) / 2`, producing `-3, -2, -1, 0` for scores `3, 5, 7, 9`. A later D&D-trained checkpoint used `(score - 11) / 2`, fixing the negative side while breaking positive even scores.

The final policy therefore splits the exact 3-to-18 table into negative-floor and nonnegative kernels. Repetition catches hidden state without extending the public contract beyond scores that an ability can generate.
