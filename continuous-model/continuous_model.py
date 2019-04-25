import exception_classes as ex


class MMc_WeightedBusyTimeAnalyzer(object):

    def __init__(self, lambda_, mu_, c, n1=1, n2=1):
        """
        Models an M/M/c queue.

        :param lambda_:
        :param mu_:
        :param c:
        """
        self.n2 = n2
        self.n1 = n1
        self.c = c
        self.mu_ = mu_
        self.lambda_ = lambda_
        if lambda_ < c * mu_:
            raise ex.UnboundedExpectedValue()

    def p_dep(self, k):
        """
        Probability of a departure if there are currently k active servers.

        :param k:
        :return:
        """
        if 1 > k > self.c:
            raise ex.KOutofRange()
        return k * self.mu_ / (self.lambda_ + k * self.mu_)

    def p_arr(self, k):
        """
        Probability of an arrival if there are currently k active servers.

        :param k:
        :return:
        """
        if 1 > k > self.c:
            raise ex.KOutofRange()
        return self.lambda_ / (self.lambda_ + k * self.mu_)

    def func_delta_der0(self, k, s, current_n1=None, current_n2=None):
        """
        Recursive definition of the LST of the weighted busy time starting from k busy servers.

        :param k:
        :param s:
        :param current_n1:
        :param current_n2:
        :return:
        """
        if current_n1 is None:
            current_n1 = self.n1
        if current_n2 is None:
            current_n2 = self.n2
        if k == 1:
            return
        if k == self.c:
            # TODO: this can have multiple values based on the 0th order derivate of etha_c (s). we cannot discard values here,
            # only we have the negativity / positivity constraints at the 1st and 2nd order derivates of delta.
            return
        # else: 1 < k < c
        return

    def func_delta_der1(self):
        # NOTE: 1 or multiple functions based on derivate order??
        pass

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
            raise ex.UnsupportedArgumentValue()

    def func_etha_c(self, s, derivate_order=0):
        """
        LST of the busy period T_c as defined in K. Omahen, V. Marathe -- Analysis & Applications of the Delay Cycle for the M/M/c Queueing
        System. 1975.

        :param s:
        :param derivate_order:
        :return: list of values, each of them being a possible solution
        """
        if s != 0:
            raise ex.UnsupportedArgumentValue()
        if derivate_order == 0:
            return sorted([self.c * self.mu_ / self.lambda_,
                           1.0])
        elif derivate_order == 1:
            return sorted([1 / (self.lambda_ - self.c * self.mu_),
                           self.c * self.mu_ / (self.lambda_ * self.c * self.mu_ - (self.lambda_ ** 2))])
        elif derivate_order == 2:
            # TODO (NEXT!):
            return