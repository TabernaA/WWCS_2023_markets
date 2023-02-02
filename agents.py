from mesa import Agent
import numpy as np
from scipy.stats import bernoulli
from scipy.stats import beta

class Firm(Agent): 

    def __init__(self, model, quality, price, production, cost ,
                 increase_price = 0.3, decrease_price = 0.7, price_change = 0.01):
        super().__init__(model.next_id(), model)

        # Compur().__init__(model.next_id(), model)
        self.quality = quality
        self.price = price
        self.production = production
        self.initial_production = production
        self.revenue = 1
        self.net_worth = 0
        self.price_change = price_change
        self.increase_price = increase_price
        self.decrease_price = decrease_price
        self.quantity_sold = 0
        self.inventories = 0
        self.cost = cost

    def innovate(self, in_budget, quality, Z=0.3, a=3, b=3, x_low=-0.025, x_up=0.025):
    
        """ Innovation process perfomed by Firm agents.

        Args:
            in_budget       : Firms innovation budget
            prod            : Firms productivity
        Params:
            Z               : Budget scaling factor for Bernoulli draw
            a               : Alpha parameter for Beta distribution
            b               : Beta parameter for Beta distribution
            x_low           : Lower bound
            x_up            : Upper bound
        """

        p = 1 - np.exp(-Z * in_budget)
        # Bernoulli draw to determine success of innovation
        if bernoulli.rvs(p) == 1:
            # Draw change in productivity from beta distribution
            quality_change = 1 + x_low + beta.rvs(a, b) * (x_up - x_low)
            in_quality = quality_change * quality
        else:
            in_quality = 0
        #print(in_productivity)
        return in_quality

    def step(self):

        # how is the quality of new entrants decided?
        # how is the cost decided (budget)

        rd_budget = 0.05 * self.revenue
        
        innovation_quality = self.innovate(rd_budget, self.quality)

        self.quality = max(innovation_quality, self.quality)

        #self.quality = min(1, max(0, self.quality + np.random.uniform(-0.025, 0.025)))
       # print('I am ', self.unique_id, type(self) )
        # compute the revenue

        production_sold =  self.initial_production - self.production
        production_left = self.initial_production - production_sold
        self.inventories += production_left
        self.revenue = self.price *  production_sold
        profits = self.revenue - self.cost
        self.net_worth += profits

        # increase the price if  the production is 0.3 of the initial production
        if self.inventories < self.increase_price * self.initial_production:
            self.price = self.price * (1 + self.price_change)

        # decrease the price if the production is 0.3 of the initial production
        elif self.inventories > self.increase_price * self.initial_production:
            self.price = max(0.1, self.price * (1 - self.price_change))

        self.quantity_sold = (self.initial_production - self.production)
        self.production = self.initial_production   #+ self.inventories

        if  self.model.time > 1000 and self.net_worth <  -2 * self.revenue:
            self.model.bnkrupt_firms.append(self)
     






class Household(Agent):
    """
    Household  agent

    Parameters
    ----------

    """

    def __init__(self, model, budget, price_pref = 0.5, quality_pref = 0.5,
                prob_entrepreneur = 0.01):

        super().__init__(model.next_id(), model)

        self.budget = budget
        self.initial_budget = budget
        self.toy_mode = model.toy_mode
        self.step_count = 0
        self.price_pref = price_pref
        self.quality_pref = quality_pref
        self.prob_entrepreneur = prob_entrepreneur

    def step(self):

        if np.random.random() < self.prob_entrepreneur:
            self.model.new_firms += 1

            
        self.step_count += 1
        # print('I am ', self.unique_id, type(self))

        if self.toy_mode:
            firm = None
            for firm in self.model.available_firms:
                if (firm.unique_id % 2 == self.unique_id % 2) == self.step_count % 2:
                    firm.production -= 1
                    self.budget -= firm.price
                    if not self.model.G.has_edge(self, firm):
                        self.model.G.add_edge(self, firm)
                        self.model.G[self][firm]['weight'] = 0
                    self.model.G[self][firm]['weight'] += firm.price
                    if firm.production <= 0:
                        self.model.available_firms.remove(firm)
            return 


        self.budget = self.initial_budget
   
        while self.budget > 0:

            #if len(self.model.available_firms) > 0:
                # print( " I am after thelen(self.model.available_firms))
            preference = 0
            buyer = None
            for firm in self.model.available_firms:
                if firm.price <= self.budget:
                    utility = self.price_pref * firm.price + self.quality_pref * firm.quality
                    if utility > preference:
                        preference = utility
                        buyer = firm
                    

            #print(buyer)
            if buyer !=  None:
                if buyer.production > 0:
                    buyer.production -= 1 
                else:
                    buyer.inventories -= 1
                self.budget -= buyer.price
                # if add an edge between the buyer and the seller to the graph if there is no edge
                if not self.model.G.has_edge(self, buyer):
                    self.model.G.add_edge(self, buyer)
                    self.model.G[self][buyer]['weight'] = 0
                   
                # increase the link weight by the price
                self.model.G[self][buyer]['weight'] += buyer.price
            
         
                #print(buyer.production)
                #

                if (buyer.production <= 0) and (buyer.inventories <= 0):
                    self.model.available_firms.remove(buyer)
               # print(buyer.production)
            else:
                break
        