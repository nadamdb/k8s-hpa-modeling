

class MMc_Analyzer(object):

    def __init__(self, lambda_, mu_, c):
        """
        Models an M/M/c queue.

        :param lambda_:
        :param mu_:
        :param c:
        """
        if c < 2:
            raise ValueError("c must be at least 2")
        self.c = c
        self.mu_ = float(mu_)
        self.lambda_ = float(lambda_)
        if lambda_ >= c * mu_:
            raise ValueError("lamba < c * mu must be satisfied, otherwise expected value is unbounded")

    def p_dep(self, k):
        """
        Probability of a departure if there are currently k active servers.

        :param k:
        :return:
        """
        if 1 > k > self.c:
            raise ValueError("k must be between 1 and c")
        return k * self.mu_ / (self.lambda_ + k * self.mu_)

    def p_arr(self, k):
        """
        Probability of an arrival if there are currently k active servers.

        :param k:
        :return:
        """
        if 1 > k > self.c:
            raise ValueError("k must be between 1 and c")
        return self.lambda_ / (self.lambda_ + k * self.mu_)

    def func_upsilon(self, k, s, derivate_order=0):
        """
        LST of the inter-arrival time random variable if there are k busy servers.

        :param k:
        :param s:
        :return:
        """
        if derivate_order == 0:
            return (self.lambda_ + k * self.mu_) / (s + self.lambda_ + k * self.mu_)
        elif derivate_order == 1:
            return -1 / ((s + self.lambda_ + k * self.mu_) ** 2)
        elif derivate_order == 2:
            return 2 / ((s + self.lambda_ + k * self.mu_) ** 3)
        else:
            raise ValueError("Higher derivate order is not supported")

    def func_etha_c(self, s, derivate_order=0):
        """
        LST of the busy period T_c as defined in K. Omahen, V. Marathe -- Analysis & Applications of the Delay Cycle for the M/M/c Queueing
        System. 1975.

        :param s:
        :param derivate_order:
        :return: list of values, each of them being a possible solution
        """
        if s != 0:
            raise ValueError("s can only be 0")
        if derivate_order == 0:
            return sorted([self.c * self.mu_ / self.lambda_,
                           1.0])
        elif derivate_order == 1:
            # NOTE : the second element is POSITIV, its (-1)* cannot be the extected value of T_c
            return sorted([1 / (self.lambda_ - self.c * self.mu_),
                           self.c * self.mu_ / (self.lambda_ * self.c * self.mu_ - (self.lambda_ ** 2))])
        elif derivate_order == 2:
            # NOTE: the 4th element is Negative, it cannot be the second moment of T_c
            return sorted([2 * self.c * self.mu_ / ((self.c * self.mu_ - self.lambda_) ** 3),
                           2 * ((self.c * self.mu_) ** 2) / self.lambda_ / ((self.c * self.mu_ - self.lambda_) ** 3),
                           2 * self.lambda_ / ((self.lambda_ - self.c * self.mu_) ** 2),
                           -2 * self.c * self.mu_ * self.lambda_ / ((self.c * self.mu_ - self.lambda_) ** 2)])
