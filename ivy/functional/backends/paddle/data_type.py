# global
from typing import Optional, Union, Sequence, List

import paddle
import numpy as np

# local
import ivy
from ivy.func_wrapper import with_unsupported_device_and_dtypes
from ivy.functional.ivy.data_type import _handle_nestable_dtype_info
from . import backend_version


ivy_dtype_dict = {
    paddle.int8: "int8",
    paddle.int16: "int16",
    paddle.int32: "int32",
    paddle.int64: "int64",
    paddle.uint8: "uint8",
    paddle.float16: "float16",
    paddle.float32: "float32",
    paddle.float64: "float64",
    paddle.complex64: "complex64",
    paddle.complex128: "complex128",
    paddle.bool: "bool",
}

native_dtype_dict = {
    "int8": paddle.int8,
    "int16": paddle.int16,
    "int32": paddle.int32,
    "int64": paddle.int64,
    "uint8": paddle.uint8,
    "float16": paddle.float16,
    "float32": paddle.float32,
    "float64": paddle.float64,
    "complex64": paddle.complex64,
    "complex128": paddle.complex128,
    "bool": paddle.bool,
}


class Finfo:
    def __init__(self, paddle_finfo: np.finfo):
        self._paddle_finfo = paddle_finfo

    def __repr__(self):
        return repr(self._paddle_finfo)

    @property
    def bits(self):
        return self._paddle_finfo.bits

    @property
    def eps(self):
        return float(self._paddle_finfo.eps)

    @property
    def max(self):
        return float(self._paddle_finfo.max)

    @property
    def min(self):
        return float(self._paddle_finfo.min)

    @property
    def smallest_normal(self):
        return float(self._paddle_finfo.tiny)


class Iinfo:
    def __init__(self, paddle_iinfo: np.iinfo):
        self._paddle_iinfo = paddle_iinfo

    def __repr__(self):
        return repr(self._paddle_iinfo)

    @property
    def bits(self):
        return self._paddle_iinfo.bits

    @property
    def max(self):
        return self._paddle_iinfo.max

    @property
    def min(self):
        return self._paddle_iinfo.min


class Bfloat16Finfo:
    def __init__(self):
        self.resolution = 0.01
        self.bits = 16
        self.eps = 0.0078125
        self.max = 3.38953e38
        self.min = -3.38953e38
        self.tiny = 1.17549e-38

    def __repr__(self):
        return "finfo(resolution={}, min={}, max={}, dtype={})".format(
            self.resolution, self.min, self.max, "bfloat16"
        )


# Array API Standard #
# -------------------#


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def astype(
    x: paddle.Tensor,
    dtype: paddle.dtype,
    /,
    *,
    copy: bool = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    dtype = ivy.as_native_dtype(dtype)
    if x.dtype == dtype:
        return x.clone() if copy else x
    return x.cast(dtype)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def broadcast_arrays(*arrays: paddle.Tensor) -> List[paddle.Tensor]:
    if len(arrays) > 1:
        desired_shape = ivy.broadcast_shapes(arrays[0].shape, arrays[1].shape)
        if len(arrays) > 2:
            with ivy.ArrayMode(False):
                for i in range(2, len(arrays)):
                    desired_shape = ivy.broadcast_shapes(
                        [desired_shape, arrays[i].shape]
                    )
    else:
        return [arrays[0]]
    result = []
    with ivy.ArrayMode(False):
        for tensor in arrays:
            result.append(broadcast_to(tensor, desired_shape))
    return result


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def broadcast_to(
    x: paddle.Tensor,
    /,
    shape: Union[ivy.NativeShape, Sequence[int]],
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    for i, dim in enumerate(shape):
        if dim < 0:
            shape[i] = x.shape[i]
    if x.ndim == 0:
        if len(shape) == 0:
            return x
        else:
            with ivy.ArrayMode(False):
                x = ivy.expand_dims(x, axis=0)
    if x.ndim > len(shape):
        x = x.reshape([-1])

    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
    ]:
        return paddle.broadcast_to(x.cast("float32"), shape).cast(x.dtype)
    elif x.dtype in [paddle.complex64, paddle.complex128]:
        x_real = paddle.broadcast_to(x.real(), shape)
        x_imag = paddle.broadcast_to(x.imag(), shape)
        return x_real + 1j * x_imag
    else:
        return paddle.broadcast_to(x, shape)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
@_handle_nestable_dtype_info
def finfo(type: Union[paddle.dtype, str, paddle.Tensor], /) -> Finfo:
    if isinstance(type, paddle.Tensor):
        type = str(type.dtype)[7:]
    elif isinstance(type, paddle.dtype):
        type = str(type)[7:]

    if ivy.as_native_dtype(type) == paddle.bfloat16:
        return Finfo(Bfloat16Finfo())

    return Finfo(np.finfo(type))


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
@_handle_nestable_dtype_info
def iinfo(type: Union[paddle.dtype, str, paddle.Tensor], /) -> Iinfo:
    if isinstance(type, paddle.Tensor):
        type = str(type.dtype)[7:]
    elif isinstance(type, paddle.dtype):
        type = str(type)[7:]

    return Iinfo(np.iinfo(type))


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def result_type(*arrays_and_dtypes: Union[paddle.Tensor, paddle.dtype]) -> ivy.Dtype:
    return ivy.promote_types(arrays_and_dtypes[0].dtype, arrays_and_dtypes[1].dtype)


# Extra #
# ------#


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def as_ivy_dtype(dtype_in: Union[paddle.dtype, str, bool, int, float], /) -> ivy.Dtype:
    if dtype_in is int:
        return ivy.default_int_dtype()
    if dtype_in is float:
        return ivy.default_float_dtype()
    if dtype_in is complex:
        return ivy.default_complex_dtype()
    if dtype_in is bool:
        return ivy.Dtype("bool")
    if isinstance(dtype_in, str):
        if dtype_in in native_dtype_dict:
            return ivy.Dtype(dtype_in)
        else:
            raise ivy.utils.exceptions.IvyException(
                "Cannot convert to ivy dtype."
                f" {dtype_in} is not supported by Paddle backend."
            )
    return ivy.Dtype(ivy_dtype_dict[dtype_in])


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def as_native_dtype(
    dtype_in: Union[paddle.dtype, str, bool, int, float]
) -> paddle.dtype:
    if dtype_in is int:
        return ivy.default_int_dtype(as_native=True)
    if dtype_in is float:
        return ivy.default_float_dtype(as_native=True)
    if dtype_in is complex:
        return ivy.default_complex_dtype(as_native=True)
    if dtype_in is bool:
        return paddle.bool
    if not isinstance(dtype_in, str):
        return dtype_in
    if dtype_in in native_dtype_dict.keys():
        return native_dtype_dict[ivy.Dtype(dtype_in)]
    else:
        raise ivy.utils.exceptions.IvyException(
            "Cannot convert to Paddle dtype." f" {dtype_in} is not supported by Paddle."
        )


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def dtype(x: paddle.Tensor, *, as_native: bool = False) -> ivy.Dtype:
    if as_native:
        return ivy.to_native(x).dtype
    return as_ivy_dtype(x.dtype)


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def dtype_bits(dtype_in: Union[paddle.dtype, str], /) -> int:
    dtype_str = as_ivy_dtype(dtype_in)
    if "bool" in dtype_str:
        return 1
    return int(
        dtype_str.replace("paddle.", "")
        .replace("uint", "")
        .replace("int", "")
        .replace("bfloat", "")
        .replace("float", "")
        .replace("complex", "")
    )


def is_native_dtype(dtype_in: Union[paddle.dtype, str], /) -> bool:
    if dtype_in in ivy_dtype_dict:
        return True
    else:
        return False
