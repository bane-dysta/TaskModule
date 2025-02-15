Multiwfn *.fchk < ESPext.txt
mv -f vtx.pdb vtx1.pdb
mv -f mol.pdb mol1.pdb

Multiwfn *.fchk -ESPrhoiso 0.001 < ESPiso.txt
mv -f density.cub density1.cub
mv -f totesp.cub ESP1.cub

Multiwfn *.fchk < ESPpt.txt
mv -f vtx.pdb vtx1.pdb
mv -f mol.pdb mol1.pdb
