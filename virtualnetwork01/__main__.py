import vnetStack
import pdnszStack

stack = vnetStack
stack.vnet.id.apply(lambda id: print(id))
