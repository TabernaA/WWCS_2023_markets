from mesa import Model
from mesa.time import RandomActivationByType, BaseScheduler
from mesa.space import  MultiGrid
from mesa.datacollection import DataCollector
from agents import Firm, Household
import networkx as nx
import numpy as np

class Market(Model):
    """Model class for the Market model. """

    def __init__(self, F=50, H=300, firms_production=1200,
                    min_income = 0, max_income = 2, min_quality = 0, 
                    max_quality = 1, decrease_price = 0.7, increase_price = 0.3, price_change = 0.01,
                    toy_mode=False
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

        # Number of agents for initialization
        self.init_n_firms = F
        self.init_n_hh = H
        self.current_id = 0
        self.graphs = [0]
        self.HHI = 0
        self.diff = 0
        self.time = 0
        # Set up the  order
        self.schedule = BaseScheduler(self)
        self.grid = MultiGrid(500, 500, True)
        self.new_firms = 0 
        self.firms_production = firms_production
        self.price_change = price_change
        self.decrease_price = decrease_price
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
                    self.per_firm_cost, decrease_price = decrease_price,
                     increase_price = increase_price, price_change = price_change  )
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        # Datacollector
        self.datacollector = DataCollector(

            model_reporters= {"HHI": lambda m: m.HHI,
                            "Distance": lambda m: m.diff 
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
    
    def compute_change(self, graph_a, graph_b):
        # Make the graphs the same size
        additions = graph_b.nodes() - graph_a.nodes() 
        deletions = graph_a.nodes() - graph_b.nodes() 
        graph_a = graph_a.copy()
        graph_b = graph_b.copy()
        graph_a.add_nodes_from(additions)
        graph_b.add_nodes_from(deletions)
        # Create the adjacency matrices
        prev = nx.adjacency_matrix(graph_a).A
        curr = nx.adjacency_matrix(graph_b).A
        # Divide by two because the matrix has two entries per pair of nodes (it is undirected)
        change = sum(sum(abs(curr - prev))) / 2
        maximum = sum(sum(prev)) / 2
        return change / maximum

    def step(self):
        """
        Run one step of the model.
        """
        ''''''
        # delete firms that are bankrupt
        for i in range(len(self.bnkrupt_firms)):
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
                        self.per_firm_cost,self.decrease_price,
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
    

    
        
        tot_revenues = [agent.revenue for agent in self.schedule.agents if type(agent) is Firm]
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
        



      

        
        # plot the graph
       # nx.draw(self.G, with_labels=True)