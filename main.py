from tqec.block.enums import BlockDimension
from tqec.block.library.closed import xzz_block, zxz_block
from tqec.block.library.open import oxz_block, xoz_block, xzo_block, zxo_block
from tqec.templates.scale import LinearFunction

dimension = LinearFunction(2, 0)

block = xzz_block(dimension)
print("=" * 80)
print(f"={'FULL INSTANTIATION':^78}=")
print("=" * 80)
print(block.instantiate())

print("=" * 80)
print(f"={'INSTANTIATION WITHOUT X':^78}=")
print("=" * 80)
print(block.instantiate_without_boundary(BlockDimension.X))


print("=" * 80)
print(f"={'INSTANTIATION WITHOUT Y':^78}=")
print("=" * 80)
print(block.instantiate_without_boundary(BlockDimension.Y))


print("=" * 80)
print(f"={'INSTANTIATION WITHOUT T':^78}=")
print("=" * 80)
print(block.instantiate_without_boundary(BlockDimension.T))
