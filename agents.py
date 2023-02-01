from mesa import Agent

class Firm(Agent): 

    def __init__(self, model, quality, price, production=10,
                 increase_price = 0.3, decrease_price = 0.7, price_change = 0.01):
        super().__init__(model.next_id(), model)

        # Compur().__init__(model.next_id(), model)
        self.quality = quality
        self.price = price
        self.production = production
        self.initial_production = production
        self.revenue = 1
        self.price_change = price_change
        self.increase_price = increase_price
        self.decrease_price = decrease_price
        self.quantity_sold = 0

    def step(self):
       # print('I am ', self.unique_id, type(self) )
        # compute the revenue
        self.revenue = self.price * (self.initial_production - self.production)
        # increase the price if  the production is 0.3 of the initial production
        if self.production < self.increase_price * self.initial_production:
            self.price = self.price * (1 + self.price_change)

        # decrease the price if the production is 0.3 of the initial production
        elif self.production > self.decrease_price * self.initial_production:
            self.price = max(0.1, self.price * (1 - self.price_change))

        self.quantity_sold = (self.initial_production - self.production)
        self.production = self.initial_production


class Household(Agent):
    """
    Household  agent

    Parameters
    ----------

    """

    def __init__(self, model, budget):

        super().__init__(model.next_id(), model)

        self.budget = budget
        self.initial_budget = budget

    def step(self):
       # print('I am ', self.unique_id, type(self))

        self.budget = self.initial_budget
   
        while self.budget > 0:

            #if len(self.model.available_firms) > 0:
                # print( " I am after thelen(self.model.available_firms))
            quality = 0
            buyer = None
            for firm in self.model.available_firms:
                if (firm.quality > quality) and (firm.price <= self.budget):
                    buyer = firm
                    quality = firm.quality

            #print(buyer)
            if buyer !=  None:
                buyer.production -= 1 
                self.budget -= buyer.price
                # if add an edge between the buyer and the seller to the graph if there is no edge
                if not self.model.G.has_edge(self, buyer):
                    self.model.G.add_edge(self, buyer)
                    self.model.G[self][buyer]['weight'] = 0
                   
                # increase the link weight by the price
                self.model.G[self][buyer]['weight'] += buyer.price
            
         
                #print(buyer.production)
                #

                if buyer.production <= 0:
                    self.model.available_firms.remove(buyer)
               # print(buyer.production)
            else:
                break
        