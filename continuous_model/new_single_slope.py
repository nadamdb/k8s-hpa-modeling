import itertools
from .base_continuous_model import MMcAnalyzer


class NewSingleSlopeAnalyzer(MMcAnalyzer):

    def __init__(self, lambda_, mu_, c, solution_pair_index=0):
        """
        Corrects the previous calculation which disregarded the dependency between T_k and D_c^k

        :param lambda_:
        :param mu_:
        :param c:
        :param solution_pair_index:
        """
        super(NewSingleSlopeAnalyzer, self).__init__(lambda_, mu_, c, solution_pair_index)

    def func_delta_c(self, k, s=0, derivate_order=0):
        """


        :param k:
        :param s:
        :param derivate_order:
        :return:
        """
        if k == self.c:
            if derivate_order == 0:
                return self.func_etha(k=self.c, s=self.c * s)
            elif derivate_order == 1:
                return list(map(lambda x: x * float(self.c), self.func_etha(k=self.c, s=self.c * s, derivate_order=1)))
            else:
                raise ValueError("Higher derivate order is not supported")
        elif 1 <= k < self.c:
            upsilon = self.func_upsilon(k, k * s)
            delta_plus_1_values = self.func_delta_c(k + 1, s)
            final_result_list = []
            if derivate_order == 0:
                for delta_plus_1 in delta_plus_1_values:
                    final_result_list.append(self.p_dep(k) * upsilon /
                                             ( 1 - self.p_arr(k) * upsilon * delta_plus_1 ))
            elif derivate_order == 1:
                upsilon_der = self.func_upsilon(k, k * s, derivate_order=1)
                delta_plus_1_der_values = self.func_delta_c(k +1, s, derivate_order=1)
                for delta_plus_1, delta_plus_1_der in itertools.product(delta_plus_1_values, delta_plus_1_der_values):
                    final_result_list.append((self.p_dep(k) * upsilon_der * float(k) +
                                              self.p_dep(k) * self.p_arr(k) * (upsilon ** 2) * delta_plus_1_der ) /
                                             ( (1  -  self.p_arr(k) * upsilon * delta_plus_1 ) ** 2 ))
            else:
                raise ValueError("Higher derivate order is not supported")
            return final_result_list
        else:
            raise ValueError("k must be between 1 and c")

    def get_product(self, func, k, s, derivate_order=0, except_idx=None):
        """
        Calculates the product PI_{j=1 to k} func(j, s, derivate_order=derivate_order), but skips the indexes which are listed in
        except_idx.

        :param func: Any function with signature (k, s, derivate_order) -> list
        :param k:
        :param except_idx:
        :return:
        """
        if k < 2:
            raise ValueError("Product calculation is only possible with more than 1 functions")
        results_dict = {}
        for j in range(1, k+1):
            if except_idx is None or j not in except_idx:
                # returns an ordered list of possible solutions
                results_dict[j] = func(j, s, derivate_order=derivate_order)
        # make a list to store the product of each of the possible solutions, all of the dict values should have the same length
        products = len(list(results_dict.values())[0]) * [1.0]
        for j, results in results_dict.items():
            for solution_idx in range(0, len(products)):
                products[solution_idx] *= results[solution_idx]
        return products

    def get_derivate_of_products(self, func, k, s):
        """
        Calculates the d/ds {func(1,s) * func(2,s) * ... * func(k,s)} derivate.

        :param func: Any function with signature (k, s, derivate_order) -> list
        :param k:
        :param s:
        :return:
        """
        derived_sum_products = []
        for i in range(1, k+1):
            products = self.get_product(func, k, s, derivate_order=0, except_idx=[i])
            derivates = func(i, s, derivate_order=1)
            if len(derivates) != len(products):
                raise NotImplementedError("Different sizes of result sets of the first and 0th derivate is not implemented")
            if len(derived_sum_products) == 0:
                for der, prod in zip(derivates, products):
                    derived_sum_products.append(der * prod)
            else:
                for solution_idx in range(0, len(derived_sum_products)):
                    derived_sum_products[solution_idx] += derivates[solution_idx] * products[solution_idx]
        return derived_sum_products

    def get_sum_of_first_derivates(self, func, k, s, list_func=True):
        """
        Sum of the first of func with arguments 1 to k, with fix s.

        :param func: Any function with signature (k, s, derivate_order) -> list | float
        :param k:
        :param s:
        :param list_func: if func returns float
        :return:
        """
        results = []
        for i in range(1, k+1):
            if len(results) == 0:
                if list_func:
                    for der in func(i, s, derivate_order=1):
                        results.append(der)
                else:
                    results.append(func(i, s, derivate_order=1))
            else:
                derivates = func(i, s, derivate_order=1)
                if list_func and len(derivates) != len(results):
                    raise NotImplementedError("Different sizes of result sets of the first derivate is not implemented")
                for solution_idx in range(0, len(results)):
                    if list_func:
                        results[solution_idx] += derivates[solution_idx]
                    else:
                        results[solution_idx] += derivates
        return results


if __name__ == '__main__':
    l = 2.8
    m = .1
    c = 29
    for k in range(1, 30):
        for solution_idx in (0, ):
            # print "\nSolution index: %s"%solution_idx
            analyzer = NewSingleSlopeAnalyzer(lambda_=l, mu_=m, c=c, solution_pair_index=solution_idx)
            print("lambda / (c * mu): %s" % (l/float(c * m)))
            # print "Expected value of interevent time I_%s: %s" % (k, -1.0 * analyzer.func_upsilon(k, 0, derivate_order=1))
            # print "Expected value of T_%s: %s" % (k, map(lambda x: -1.0*x, analyzer.func_etha(k, 0, derivate_order=1)))
            # print "Expected value of the area under %s-%s transition: %s" % (k, k-1, map(lambda x: -1.0*x,
            #                                                                            analyzer.func_delta_c(k, 0, derivate_order=1)))
            sum_func_etha_0 = analyzer.get_sum_of_first_derivates(analyzer.func_etha, k, 0)
            sum_func_delta_c_0 = analyzer.get_sum_of_first_derivates(analyzer.func_delta_c, k, 0)
            print("[SUM_E]Expected value of Summa {i=1 to %s} T_i: %s" % (k, list(map(lambda x: -1.0*x, sum_func_etha_0))))
            print("[SUM_E]Expected value of a slope from state %s: %s" % (k, list(map(lambda x: -1.0 * x, sum_func_delta_c_0))))
            # print "[SUM_E]Expected value of Summa {i=1 to %s} I_i: %s" % (k, map(lambda x: -1.0 * x,
            #                                                               analyzer.get_sum_of_first_derivates(analyzer.func_upsilon, k, 0,
            #                                                                                                   list_func=False)))
            print("[SUM_E]Time-independent utilization approx: %s" % (list(map(lambda t: t[0]/t[1]/float(analyzer.c),
                                                                      zip(sum_func_delta_c_0, sum_func_etha_0)))))
            # if k > 1:
            #     sum_func_etha_0 = analyzer.get_derivate_of_products(analyzer.func_etha, k, 0)
            #     sum_func_delta_c_0 = analyzer.get_derivate_of_products(analyzer.func_delta_c, k, 0)
            #     print "[DER OF PROD]Expected value of Summa {i=1 to %s} T_i: %s" % (k, map(lambda x: -1.0*x, sum_func_etha_0))
            #     print "[DER OF PROD]Expected value of a slope from state %s: %s" % (k, map(lambda x: -1.0 * x, sum_func_delta_c_0))
            #     print "[DER OF PROD]Time-independent utilization approx: %s" % (map(lambda t: t[0] / t[1] / float(analyzer.c),
            #                                                                     zip(sum_func_delta_c_0, sum_func_etha_0)))