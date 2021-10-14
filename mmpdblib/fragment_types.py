# mmpdb - matched molecular pair database generation and analysis
#
# Copyright (c) 2015-2017, F. Hoffmann-La Roche Ltd.
# Copyright (c) 2021, Andrew Dalke Scientific AB
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#    * Neither the name of F. Hoffmann-La Roche Ltd. nor the names of
#      its contributors may be used to endorse or promote products
#      derived from this software without specific prior written
#      permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import registry
from sqlalchemy.orm import relationship

mapper_registry = registry()
Base = mapper_registry.generate_base()

class FragmentOptions(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True)
    version = Column(Integer)
    cut_smarts = Column(String(1000))
    max_heavies = Column(Integer)
    max_rotatable_bonds = Column(Integer)
    method = Column(String(20))
    num_cuts = Column(Integer)
    rotatable_smarts = Column(String(1000))
    salt_remover = Column(String(200))
    min_heavies_per_const_frag = Column(Integer)


    def to_dict(self):
        d = {}
        for name in ("max_heavies", "max_rotatable_bonds", "rotatable_smarts",
                     "cut_smarts", "num_cuts", "method", "salt_remover",
                     "min_heavies_per_const_frag"):
            d[name] = getattr(self, name)
        return d
    
    def to_text_settings(self):
        def _none(x):
            return "none" if x is None else str(x)
        return (
            ("max_heavies", _none(self.max_heavies)),
            ("max_rotatable_bonds", _none(self.max_rotatable_bonds)),
            ("rotatable_smarts", self.rotatable_smarts),
            ("cut_smarts", self.cut_smarts),
            ("num_cuts", str(self.num_cuts)),
            ("method", self.method),
            ("salt_remover", self.salt_remover),
            ("min_heavies_per_const_frag", str(self.min_heavies_per_const_frag))

            )
    

class FragmentErrorRecord(Base):
    __tablename__ = "error_record"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False, index=True)
    input_smiles = Column(String(300), nullable=False)
    errmsg = Column(String(100))

    def __repr__(self):
        return f"FragmentErrorRecord({self.title!r}, {self.input_smiles!r}, {self.errmsg!r})"

class FragmentRecord(Base):
    __tablename__ = "record"
    
    errmsg = None # make it easier to test if this is a FragmentErrorRecord
    
    id  = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False, index=True)
    input_smiles = Column(String(400), nullable=False)
    num_normalized_heavies = Column(Integer)
    normalized_smiles = Column(String(350), nullable=False)

    fragmentations = relationship("Fragmentation", back_populates="record")

    def __repr__(self):
        return (f"FragmentRecord({self.title!r}, {self.input_smiles!r}, "
                f"{self.num_normalized_heavies}, {self.normalized_smiles!r}, "
                f"{self.fragmentations})")

class Fragmentation(Base):
    __tablename__ = "fragmentation"
    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("record.id"), index=True)
    num_cuts = Column(Integer)
    enumeration_label = Column(String(1), nullable=False)
    variable_num_heavies = Column(Integer)
    variable_symmetry_class = Column(String(3), nullable=False)
    variable_smiles = Column(String(350), nullable=False)
    attachment_order = Column(String(3), nullable=False)
    constant_num_heavies = Column(Integer)
    constant_symmetry_class = Column(String(3), nullable=False)
    constant_smiles = Column(String(350), nullable=False)
    constant_with_H_smiles = Column(String(350))

    record = relationship("FragmentRecord", back_populates="fragmentations")
    
    def __repr__(self):
        return (
            f"Fragmentation({self.num_cuts}, {self.enumeration_label!r}, "
            f"{self.variable_num_heavies}, {self.variable_symmetry_class!r}, "
            f"{self.variable_smiles!r}, {self.attachment_order!r}, "
            f"{self.constant_num_heavies}, {self.constant_symmetry_class!r}, "
            f"{self.constant_smiles!r}, {self.constant_with_H_smiles!r})"
            )

    def get_unique_key(self):
        return "%s.%s.%s" % (self.attachment_order, self.variable_smiles, self.constant_smiles)
    
####

class FragmentValueError(ValueError):
    def __init__(self, name, value, reason):
        self.name = name
        self.value = value
        self.reason = reason

    def __str__(self):
        return "Error with %s (%r): %s" % (self.name, self.value, self.reason)

    def __repr__(self):
        return "FragmentValueError(%r, %r, %r)" % (
            self.name, self.value, self.reason)


class FragmentFormatError(ValueError):
    def __init__(self, reason, location):
        self.reason = reason
        self.location = location

    def __repr__(self):
        return "FragmentFormatError(%r, %r)" % (
            self.reason, self.location)
    
    def __str__(self):
        return "%s, %s" % (self.reason, self.location.where())
