import vnetStack
import pdnszStack
import stStack
import monitorStack

stack = vnetStack
stack.vnet.id.apply(lambda id: print(id))
stack.snet_dict["snet-pep"]