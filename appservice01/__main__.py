import vnetStack
import pdnszStack
import stStack
import aspStack
import appStack
import kvStack

stack = vnetStack
stack.vnet.id.apply(lambda id: print(id))
stack.snet_dict["snet-pep"]
