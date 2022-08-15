import smartpy as sp

class Test(sp.Contract):
    def __init__(self):

        # Storage

        self.init(
            admin = sp.test_account("admin").address,
            cost = sp.tez(1), # cost of a visit
            visited = sp.map(l = {}, tkey = sp.TAddress, tvalue = sp.TNat), # to keep track how many time an address has visited 
            registration = sp.map(l = {}, tkey = sp.TAddress, tvalue = sp.TBool), #to keep track an address is registred
            checkTime = sp.map(l = {}, tkey = sp.TAddress, tvalue = sp.TTimestamp), #to keep track on time
        )
    
    @sp.entry_point
    def register(self):

        # Storage changes

        self.data.registration[sp.sender]=True
        self.data.visited[sp.sender]=0
       
    @sp.entry_point
    def visit(self):

        # --- Assertion --- 
        
        # Check if the map contains the address, otherwise, the user didn't registered yet
        sp.verify(self.data.registration.contains(sp.sender), "Please register first")

        # Check if the user is paying enough XTZ
        sp.verify(sp.amount >= self.data.cost, "Not enough, you have to pay 1 XTZ")

        sp.if self.data.visited[sp.sender] == 0 :
            self.data.checkTime[sp.sender] = sp.now

        sp.if self.data.visited[sp.sender] > 0 :
            sp.verify(sp.now >= self.data.checkTime[sp.sender].add_seconds(60), "You have to wait 1 minute")
            self.data.checkTime[sp.sender] = sp.now

        # Keep track of how many visits for each address
        self.data.visited[sp.sender] = self.data.visited[sp.sender] + 1

        # Return extra XTZ
        extra_amount = sp.amount - self.data.cost 
        sp.if extra_amount > sp.tez(0):
            sp.send(sp.sender, extra_amount)

    @sp.entry_point
    def withdraw(self):

        # Assertion -- Check if its the admin
        sp.verify(sp.sender == self.data.admin, "You're not the admin, you cannot withdraw the funds")

        #send the tez to the admin 
        sp.send(self.data.admin, sp.balance)

@sp.add_test(name = "main")
def test():

    scenario = sp.test_scenario()

    # Testing Accounts
    admin = sp.test_account("admin")
    account1 = sp.test_account("account1")
    account2 = sp.test_account("account2")
    account3 = sp.test_account("account3")

    # Instance of the contract 
    test = Test()
    scenario += test


    # --------REGISTER--------


    # Register account 1  
    scenario += test.register().run(sender = account1)

    # Register account 2  
    scenario += test.register().run(sender = account2)
    
    # Register admin  
    scenario += test.register().run(sender = admin)

    # Register account 2 a second time (nothing happens)
    scenario += test.register().run(sender = account2)


    # --------VISIT--------


    # Call visit without paying 1 XTZ 
    scenario += test.visit().run(
        sender = account1, now = sp.now, amount = sp.tez(0), valid = False
    )

    # Call visit without registering
    scenario += test.visit().run(
        sender = account3, now = sp.now, amount = sp.tez(1), valid = False
    )
    
    # Call visit with more than 1 XTZ to check if it returns extra XTZ
    scenario += test.visit().run(
        sender = account1, now = sp.now, amount = sp.tez(2)
    )

    # Call visit again without waiting 1 minute (same account, visit for the second time)
    scenario += test.visit().run(
        sender = account1, now = sp.now.add_seconds(20), amount = sp.tez(1), valid = False
    )

    # Call with same account but waiting more than 1 minute
    scenario += test.visit().run(
        sender = account1, now = sp.now.add_minutes(2), amount = sp.tez(1)
    )

    # Call visit with account2
    scenario += test.visit().run(
        sender = account2, now = sp.now, amount = sp.tez(1)
    )

    # Call visit with account2 for the SECOND time without waiting 1 minute
    scenario += test.visit().run(
        sender = account2, now = sp.now.add_seconds(30), amount = sp.tez(1), valid = False
    )

    # Call visit with account2 for the SECOND time after waiting 1 minute
    scenario += test.visit().run(
        sender = account2, now = sp.now.add_minutes(1), amount = sp.tez(1)
    )

    # Call visit with account2 for the THIRD time without waiting 1 minute
    scenario += test.visit().run(
        sender = account2, now = sp.now.add_seconds(59), amount = sp.tez(1), valid = False
    )

    # Call visit with account2 for the THIRD time after waiting 1 minute
    scenario += test.visit().run(
        sender = account2, now = sp.now.add_minutes(1), amount = sp.tez(1)
    )


    # --------WITHDRAW--------

    # Call withdraw from another account
    scenario += test.withdraw().run(sender = account1, valid = False)

    # Call withdraw from admin
    scenario += test.withdraw().run(sender = admin)

    # Register account 3 just to check that the balance of the contract is now 0 :)
    scenario += test.register().run(sender = account3)


