from mesa import Agent
import numpy as np
from scipy.stats import bernoulli
from scipy.stats import beta

class Firm(Agent): 

    def __init__(self, model, quality, price, production, cost ,
                 increase_price = 0.3, price_change = 0.01):
        super().__init__(model.next_id(), model)

        # Compur().__init__(model.next_id(), model)
        self.quality = quality
        self.price = price
        self.production = production
        self.initial_production = production
        self.revenue = 1
        self.net_worth = 3000
        self.price_change = price_change
        self.increase_price = increase_price
        self.quantity_sold = 0
        self.inventories = 0
        self.cost = cost * 0.8
        self.rd_share = 0.05

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

        rd_budget = self.rd_share * self.revenue

        if self.model.time > self.model.time_collusion:
            self.rd_share = 0.975 * self.rd_share
            self.price_change = 0.975 * self.price_change
        
        
        innovation_quality = self.innovate(rd_budget, self.quality)

        

        self.quality = max(innovation_quality, self.quality)

        #self.quality = min(1, max(0, self.quality + np.random.uniform(-0.025, 0.025)))
       # print('I am ', self.unique_id, type(self) )
        # compute the revenue

        production_sold =  self.initial_production - self.production
        production_left = self.initial_production - production_sold
        self.inventories += production_left
        self.inventories = min(self.inventories, self.initial_production * 0.5)
        self.revenue = self.price *  production_sold
        profits = self.revenue - self.cost
        self.net_worth += profits

        if self.model.time > self.model.time_collusion and self.model.time <  self.model.time_collusion + 10:
            self.price = self.price * (1 + self.price_change/10)




        # increase the price if  the production is 0.3 of the initial production
        if self.inventories < self.increase_price * self.initial_production:
            self.price = self.price * (1 + self.price_change)

        # decrease the price if the production is 0.3 of the initial production
        elif self.inventories > self.increase_price * self.initial_production:
            self.price = max(0.1, self.price * (1 - self.price_change))

        self.quantity_sold = (self.initial_production - self.production)
        self.production = self.initial_production   #+ self.inventories

        if  self.model.time > 100 and self.net_worth <  -2 * self.revenue:
            if self.model.time < self.model.time_collusion:
                self.model.bnkrupt_firms.append(self)
     






class Household(Agent):
    """
    Household  agent

    Parameters
    ----------

    """

    def __init__(self, model, budget, price_pref = 0.5, quality_pref = 0.5,
                prob_entrepreneur = 0.001):

        super().__init__(model.next_id(), model)

        self.budget = budget
        self.initial_budget = budget
        self.toy_mode = model.toy_mode
        self.step_count = 0
        self.price_pref = price_pref
        self.quality_pref = quality_pref
        self.prob_entrepreneur = prob_entrepreneur
        self.buyer = None

    def step(self):

        if self.model.time < self.model.time_collusion:

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

            preference = 0
            buyer = None
            for firm in self.model.available_firms:
                if firm.price <= self.budget:
                    utility_new_buyer = self.price_pref * firm.price + self.quality_pref * firm.quality
                    if utility_new_buyer > preference:
                        preference = utility_new_buyer
                        buyer = firm
                    
            
            #print(buyer)
         
            if buyer !=  None:

                # if I can choose from two buyers
                if self.buyer != None and self.buyer != buyer and self.buyer <= self.budget:
                    # if the old buyer is still available
                    if self.buyer in self.model.available_firms:
                    # utility of other buyer is now:
                        utility_current_buyer = self.price_pref * self.buyer.price + self.quality_pref * self.buyer.quality
                        # has the new buyer a higher utility?
                        if utility_new_buyer > utility_current_buyer:
                            # probability of switching to the other buyer
                            prob = 1 - np.exp(1  * (utility_current_buyer - utility_new_buyer) / utility_current_buyer)
                            if np.random.random() < prob:
                                self.buyer = buyer
                                buyer = self.buyer

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
        