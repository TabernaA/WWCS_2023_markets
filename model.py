from mesa import Model
from mesa.time import  BaseScheduler
from mesa.space import  MultiGrid
from mesa.datacollection import DataCollector
from agents import Firm, Household
import networkx as nx
import numpy as np

class Market(Model):
    """Model class for the Market model. """

    def __init__(self, F=50, H=500, firms_production=12,
                    min_income = 0, max_income = 10, min_quality = 0, 
                    max_quality = 1, increase_price = 0.1, price_change = 0.01,
                    seed = 0, time_collusion = 500, toy_mode=False
                 ):
        """Initialization of the CRAB model.

        Args:
            F                  : Number of  firm agents
            H                   : Number of household agents
        """
        self.toy_mode = toy_mode
        if toy_mode:
            F = 2
            H = 2
            firms_production = 1
        # regulate stochasticity
        np.random.seed(int(seed))
        self.reset_randomizer(seed)
        self.running = True

        # Number of agents for initialization
        self.init_n_firms = F
        self.init_n_hh = H
        self.current_id = 0
        self.graphs = [0]
        self.HHI = 0
        self.diff = 0
        self.time = 0

        self.revenues = [0]
        
        self.total_revenue = 0
        self.average_price = 1
        self.average_quality = 0.5
        self.number_of_firms = F
        self.time_collusion = time_collusion
        # Set up the  order
        self.schedule = BaseScheduler(self)
        self.grid = MultiGrid(500, 500, True)
        self.new_firms = 0 
        self.firms_production = firms_production
        self.price_change = price_change
        self.increase_price = increase_price
        self.bnkrupt_firms = []



        self.per_firm_cost = H * ((max_income - min_income) * 0.5) / F 


        # create households
        for j in range(self.init_n_hh):

            income =  np.random.uniform(min_income, max_income)
            price_pref = np.random.uniform(0, 1)
            quality_pref = np.random.uniform(0, 1)
            a = Household(self, income, price_pref, quality_pref)
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        # Create firms
        for i in range(self.init_n_firms):

            quality = np.random.uniform(min_quality, max_quality)
            price = 1
            a = Firm(self, quality, price,firms_production,
                    self.per_firm_cost,
                     increase_price = increase_price,
                    price_change = price_change  )
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        # Datacollector
        self.datacollector = DataCollector(

            model_reporters= {"HHI": HHI,
                            "Distance": diff,
                            "Reveneue": total_revenue,
                            "Average_price": average_price,
                            "Average_quality": average_quality,
                            "Number_of_firms": number_of_firms,

                            },
            agent_reporters={"Type": lambda a: type(a).__name__,
                             "Quality": lambda a: a.quality if type(a) is Firm else None,
                             "Revenue": lambda a: a.revenue if type(a) is Firm else None,
                             "Quantity_sold": lambda a: a.quantity_sold if type(a) is Firm else None,
                             "Price": lambda a: a.price if type(a) is Firm else None,
                            "Net_worth": lambda a: a.net_worth if type(a) is Firm else None,
                            "Initial_budget": lambda a: a.initial_budget if type(a) is Household else None,
                             "budget": lambda a: a.budget if type(a) is Household else None
                             }


        )
    
    def compute_change(graph_a, graph_b):
        # Make the graphs the same size
        additions = graph_b.nodes() - graph_a.nodes() 
        deletions = graph_a.nodes() - graph_b.nodes() 
        graph_a = self.refresh_graph(graph_a, additions)
        graph_b = self.refresh_graph(graph_b, deletions)    
        prev = nx.adjacency_matrix(graph_a).A
        curr = nx.adjacency_matrix(graph_b).A
        change = sum(sum(abs(curr - prev)))
        maximum = sum(sum(prev))
        return change / maximum

    def step(self):
        """
        Run one step of the model.
        """
        ''''''
        # delete firms that are bankrupt
        for i in range(len(self.bnkrupt_firms)):
            if len(self.schedule.agents) > 5:
                self.schedule.remove(self.bnkrupt_firms[i])
                self.grid.remove_agent(self.bnkrupt_firms[i])
        self.bnkrupt_firms = []
        # add new firms
        self.available_firms = [
            agent for agent in self.schedule.agents if type(agent) is Firm]

        if self.time > 100:

            for i in range(self.new_firms):
                new_firm =  np.random.choice(self.available_firms)
                quality = new_firm.quality
                price = new_firm.price
                a = Firm(self, quality, price,self.firms_production,
                        self.per_firm_cost,
                        self.increase_price, self.price_change  )
                self.schedule.add(a)
                a.net_worth = 3500
                a.revenue = 0
                a.quantity_sold = 0
                a.inventory = 0

                # Add the agent to a random grid cell
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                self.grid.place_agent(a, (x, y))
        

        # create a list with firms object
        self.available_firms = [
            agent for agent in self.schedule.agents if type(agent) is Firm]
      
        self.new_firms = 0

        # create a networkx graph where the nodes are the firms and households

        self.G = nx.Graph()
        self.G.add_nodes_from(self.schedule.agents)
        
      
        self.datacollector.collect(self)
        self.schedule.step()
        # store the graph in a list
         


        if self.time > 0:

            self.diff =  self.compute_change(self.graphs[-1], self.G)#if maximum > 0 else 0
        self.graphs.append(self.G.copy())

        self.average_price = np.mean([agent.price for agent in self.schedule.agents if type(agent) is Firm])
        self.average_quality = np.mean([agent.quality for agent in self.schedule.agents if type(agent) is Firm])
        self.number_firms = len([agent for agent in self.schedule.agents if type(agent) is Firm])
    

    
        
        tot_revenues = [agent.revenue for agent in self.schedule.agents if type(agent) is Firm]
        self.revenues = tot_revenues
        #list_hh = [agent for agent in self.schedule.agents if type(agent) is Household]
        # iterate thorugh a dictionary of agents in aa fast way
        # normalize the revenue to have a value between 0 and 1
        if sum( tot_revenues) > 0:
            revenue = [x / sum( tot_revenues) for x in  tot_revenues]
            # square the revenue
            revenue = [x ** 2 for x in revenue]
            # sum the revenue
            self.HHI = sum(revenue)
        else:
            self.HHI = 0
        self.time += 1
    
def average_price(model):
    return model.average_price
def average_quality(model):
    return model.average_quality
def number_of_firms(model):
    return model.number_of_firms
def HHI(model):
    return model.HHI
def diff(model):
    return model.diff
def total_revenue(model):
    return sum(model.revenues)




      

        
        # plot the graph
       # nx.draw(self.G, with_labels=True)
'''
            agent_reporters={"Type": lambda a: type(a).__name__,
                             "Quality": lambda a: a.quality if type(a) is Firm else None,
                             "Revenue": lambda a: a.revenue if type(a) is Firm else None,
                             "Quantity_sold": lambda a: a.quantity_sold if type(a) is Firm else None,
                             "Price": lambda a: a.price if type(a) is Firm else None,
                            "Net_worth": lambda a: a.net_worth if type(a) is Firm else None,
                            "Initial_budget": lambda a: a.initial_budget if type(a) is Household else None,
                             "budget": lambda a: a.budget if type(a) is Household else None
                             }
'''