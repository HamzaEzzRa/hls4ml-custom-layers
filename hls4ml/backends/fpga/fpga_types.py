import numpy as np

from hls4ml.model.hls_types import CompressedType, NamedType, ExponentType, FixedPrecisionType, IntegerPrecisionType, XnorPrecisionType, ExponentPrecisionType, TensorVariable, PackedType, WeightVariable

#region Precision types

class APIntegerPrecisionType(IntegerPrecisionType):
    def definition_cpp(self):
        typestring = 'ap_{signed}int<{width}>'.format(signed='u' if not self.signed else '', width=self.width)
        return typestring

    @classmethod
    def from_precision(cls, precision_type):
        return cls(width=precision_type.width, signed=precision_type.signed)

class APFixedPrecisionType(FixedPrecisionType):
    def _rounding_mode_cpp(self, mode):
        if mode is not None:
            return 'AP_' + str(mode)

    def _saturation_mode_cpp(self, mode):
        if mode is not None:
            return 'AP_' + str(mode)

    def definition_cpp(self):
        args = [self.width, self.integer, self._rounding_mode_cpp(self.rounding_mode), self._saturation_mode_cpp(self.saturation_mode), self.saturation_bits]
        args = ','.join([str(arg) for arg in args if arg is not None])
        typestring = 'ap_{signed}fixed<{args}>'.format(signed='u' if not self.signed else '', args=args)
        return typestring

    @classmethod
    def from_precision(cls, precision_type):
        return cls(width=precision_type.width, integer=precision_type.integer, signed=precision_type.signed,
            rounding_mode=precision_type.rounding_mode, saturation_mode=precision_type.saturation_mode, saturation_bits=precision_type.saturation_bits)

class APXnorPrecisionType(XnorPrecisionType):
    definition_cpp = APIntegerPrecisionType.definition_cpp

    @classmethod
    def from_precision(cls, precision_type):
        return cls()

class APExponentPrecisionType(ExponentPrecisionType):
    definition_cpp = APIntegerPrecisionType.definition_cpp

    @classmethod
    def from_precision(cls, precision_type):
        return cls(width=precision_type.width, signed=precision_type.signed)

class ACIntegerPrecisionType(IntegerPrecisionType):
    def definition_cpp(self):
        typestring = 'ac_int<{width}, {signed}>'.format(width=self.width, signed=str(self.signed).lower())
        return typestring

    @classmethod
    def from_precision(cls, precision_type):
        return cls(width=precision_type.width, signed=precision_type.signed)

class ACFixedPrecisionType(FixedPrecisionType):
    def _rounding_mode_cpp(self, mode):
        if mode is not None:
            return 'AC_' + str(mode)

    def _saturation_mode_cpp(self, mode):
        if mode is not None:
            return 'AC_' + str(mode)

    def definition_cpp(self):
        args = [self.width, self.integer, str(self.signed).lower(), self._rounding_mode_cpp(self.rounding_mode), self._saturation_mode_cpp(self.saturation_mode), self.saturation_bits]
        args = ','.join([str(arg) for arg in args if arg is not None])
        typestring = 'ac_fixed<{args}>'.format(args=args)
        return typestring

    @classmethod
    def from_precision(cls, precision_type):
        return cls(width=precision_type.width, integer=precision_type.integer, signed=precision_type.signed,
            rounding_mode=precision_type.rounding_mode, saturation_mode=precision_type.saturation_mode, saturation_bits=precision_type.saturation_bits)

class ACXnorPrecisionType(XnorPrecisionType):
    definition_cpp = ACIntegerPrecisionType.definition_cpp

    @classmethod
    def from_precision(cls, precision_type):
        return cls()

class ACExponentPrecisionType(ExponentPrecisionType):
    definition_cpp = ACIntegerPrecisionType.definition_cpp

    @classmethod
    def from_precision(cls, precision_type):
        return cls(width=precision_type.width, signed=precision_type.signed)

class PrecisionTypeConverter(object):
    def convert(self, precision_type):
        raise NotImplementedError

class APTypeConverter(PrecisionTypeConverter):
    def convert(self, precision_type):
        type_cls = type(precision_type)

        # If the type is already converted, do nothing
        if type_cls.__name__.startswith('AP'):
            return precision_type

        if type_cls == XnorPrecisionType:
            return APXnorPrecisionType.from_precision(precision_type)
        elif type_cls == IntegerPrecisionType:
            return APIntegerPrecisionType.from_precision(precision_type)
        elif type_cls == ExponentPrecisionType:
            return APExponentPrecisionType.from_precision(precision_type)
        elif type_cls == FixedPrecisionType:
            return APFixedPrecisionType.from_precision(precision_type)
        else:
            raise Exception('Cannot convert precision type to AP: {}'.format(precision_type.__class__.__name__))

class ACTypeConverter(PrecisionTypeConverter):
    def convert(self, precision_type):
        type_cls = type(precision_type)

        # If the type is already converted, do nothing
        if type_cls.__name__.startswith('AC'):
            return precision_type

        if type_cls == XnorPrecisionType:
            return ACXnorPrecisionType.from_precision(precision_type)
        elif type_cls == IntegerPrecisionType:
            return ACIntegerPrecisionType.from_precision(precision_type)
        elif type_cls == ExponentPrecisionType:
            return ACExponentPrecisionType.from_precision(precision_type)
        elif type_cls == FixedPrecisionType:
            return ACFixedPrecisionType.from_precision(precision_type)
        else:
            raise Exception('Cannot convert precision type to AC: {}'.format(precision_type.__class__.__name__))

#endregion

#region Data types

class HLSType(NamedType):
    def definition_cpp(self):
        return 'typedef {precision} {name};\n'.format(name=self.name, precision=self.precision.definition_cpp())

    @classmethod
    def from_type(cls, type, precision_converter):
        return cls(
            name=type.name,
            precision=precision_converter.convert(type.precision)
        )

class HLSCompressedType(CompressedType):
    def definition_cpp(self):
        cpp_fmt = (
            'typedef struct {name} {{'
            '{index} row_index;'
            '{index} col_index;'
            '{precision} weight; }} {name};\n'
        )
        return cpp_fmt.format(name=self.name, index=self.index_precision, precision=self.precision.definition_cpp())

    @classmethod
    def from_type(cls, type, precision_converter):
        return cls(
            name=type.name,
            precision=precision_converter.convert(type.precision),
            index_precision=type.index_precision
        )

class HLSExponentType(ExponentType):
    def definition_cpp(self):
        cpp_fmt = (
            'typedef struct {name} {{'
            '{sign} sign;'
            '{precision} weight; }} {name};\n'
        )
        return cpp_fmt.format(name=self.name, precision=self.precision.definition_cpp(), sign=str(XnorPrecisionType()))

    @classmethod
    def from_type(cls, type, precision_converter):
        return cls(
            name=type.name,
            precision=precision_converter.convert(type.precision)
        )

class HLSPackedType(PackedType):
    def definition_cpp(self):
        n_elem_expr = '/' if self.unpack else '*'
        return 'typedef nnet::array<{precision}, {n_elem}> {name};\n'.format(name=self.name, precision=self.precision.definition_cpp(), n_elem=str(self.n_elem) + n_elem_expr + str(self.n_pack))

    @classmethod
    def from_type(cls, type, precision_converter):
        return cls(
            name=type.name,
            precision=precision_converter.convert(type.precision),
            n_elem=type.n_elem,
            n_pack=type.n_pack
        )

class HLSTypeConverter(object):
    def __init__(self, precision_converter):
        self.precision_converter = precision_converter

    def convert(self, type):
        if isinstance(type, PackedType):
            return HLSPackedType.from_type(type, self.precision_converter)
        elif isinstance(type, CompressedType):
            return HLSCompressedType.from_type(type, self.precision_converter)
        elif isinstance(type, ExponentType):
            return HLSExponentType.from_type(type, self.precision_converter)
        elif isinstance(type, NamedType):
            return HLSType.from_type(type, self.precision_converter)
        else:
            raise Exception('Unknown type: {}'.format(type.__class__.__name__))

#endregion

#region Variables

class ArrayVariable(TensorVariable):
    def __init__(self, tensor_var, type_converter, pragma='partition'):
        super(ArrayVariable, self).__init__(tensor_var.shape, tensor_var.dim_names, tensor_var.name, tensor_var.type.name, tensor_var.type.precision)
        self.type = type_converter.convert(self.type)
        self.pragma = pragma

    def size_cpp(self):
        return '*'.join([str(k) for k in self.dim_names])

    @classmethod
    def from_variable(cls, tensor_var, type_converter, pragma='partition'):
        return cls(
            tensor_var,
            type_converter,
            pragma=pragma
        )

class VivadoArrayVariable(ArrayVariable):
    def definition_cpp(self, name_suffix='', as_reference=False):
        return '{type} {name}{suffix}[{shape}]'.format(type=self.type.name, name=self.cppname, suffix=name_suffix, shape=self.size_cpp())

class QuartusArrayVariable(ArrayVariable):
    def definition_cpp(self, name_suffix='', as_reference=False):
        return '{type} {name}{suffix}[{shape}] {pragma}'.format(type=self.type.name, name=self.cppname, suffix=name_suffix, shape=self.size_cpp(), pragma=self.pragma)


class StructMemberVariable(ArrayVariable):
    """Used by Quartus backend for input/output arrays that are members of the inputs/outpus struct"""
    def __init__(self, tensor_var, type_converter, pragma='hls_register', struct_name=None):
        super(StructMemberVariable, self).__init__(tensor_var, type_converter, pragma)
        assert struct_name is not None, 'struct_name must be provided when creating StructMemberVariable'
        self.struct_name = str(struct_name)
        self.member_name = self.name
        self.name = self.struct_name + '.' + self.member_name

    def definition_cpp(self, name_suffix='', as_reference=False):
        return '{type} {name}{suffix}[{shape}]'.format(type=self.type.name, name=self.member_name, suffix=name_suffix, shape=self.size_cpp())

    @classmethod
    def from_variable(cls, tensor_var, type_converter, pragma='partition', struct_name=None):
        if type(tensor_var) == cls:
            return tensor_var
        return cls(
            tensor_var,
            type_converter,
            pragma=pragma,
            struct_name=struct_name
        )

class StreamVariable(TensorVariable):
    def __init__(self, tensor_var, type_converter, n_pack=1, depth=0):
        super(StreamVariable, self).__init__(tensor_var.shape, tensor_var.dim_names, tensor_var.name, tensor_var.type.name, tensor_var.type.precision)
        self.type = type_converter.convert(PackedType(self.type.name, self.type.precision, self.shape[-1], n_pack))
        if depth == 0:
            depth = np.prod(self.shape) // self.shape[-1]
        self.pragma = ('stream', depth)

    def get_shape(self):
        return zip(self.dim_names, self.shape)

    def size_cpp(self):
        return '*'.join([str(k) for k in self.dim_names])

    def definition_cpp(self, name_suffix='', as_reference=False):
        if as_reference: # Function parameter
            return 'hls::stream<{type}> &{name}{suffix}'.format(type=self.type.name, name=self.cppname, suffix=name_suffix)
        else: # Declaration
            return 'hls::stream<{type}> {name}{suffix}("{name}")'.format(type=self.type.name, name=self.cppname, suffix=name_suffix)

    @classmethod
    def from_variable(cls, tensor_var, type_converter,  n_pack=1, depth=0):
        if type(tensor_var) == cls:
            return tensor_var
        return cls(
            tensor_var,
            type_converter,
            n_pack=n_pack,
            depth=depth
        )

class StaticWeightVariable(WeightVariable):
    def __init__(self, weight_var, type_converter):
        super(StaticWeightVariable, self).__init__(weight_var.name, weight_var.type.name, weight_var.type.precision, weight_var.data)
        self.weight_class = weight_var.__class__.__name__
        self.type = type_converter.convert(self.type)

    def definition_cpp(self, name_suffix='', as_reference=False):
        return '{type} {name}[{size}]'.format(type=self.type.name, name=self.cppname, size=self.data_length)

    @classmethod
    def from_variable(cls, weight_var, type_converter):
        if type(weight_var) == cls:
            return weight_var
        return cls(
            weight_var,
            type_converter=type_converter
        )

class BramWeightVariable(WeightVariable):
    @classmethod
    def from_variable(cls, weight_var):
        if type(weight_var) == cls:
            return weight_var
        return cls(
            var_name=weight_var.name,
            type_name=weight_var.type.name,
            precision=weight_var.type.precision,
            data=weight_var.data,
            quantizer=weight_var.quantizer
        )

#endregion