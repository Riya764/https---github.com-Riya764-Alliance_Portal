from collections import OrderedDict

#=========================================================================
# Csv file fields dictonary
#=========================================================================

PRODUCT_FIELDS = OrderedDict()
PRODUCT_FIELDS['category'] = {"label": "CATEGORY"}
PRODUCT_FIELDS['brand'] = {"label": "BRAND CODE"}
PRODUCT_FIELDS['basepack_name'] = {"label": "BASEPACK NAME"}
PRODUCT_FIELDS['basepack_code'] = {"label": "BASEPACK CODE"}
PRODUCT_FIELDS['basepack_size'] = {"label": "BASEPACK SIZE"}
PRODUCT_FIELDS['unit'] = {"label": "UNIT"}
PRODUCT_FIELDS['expiry_day'] = {"label": "EXPIRY IN(DAYS)"}
PRODUCT_FIELDS['cld_configuration'] = {"label": "CLD CONFIGURATION"}
PRODUCT_FIELDS['mrp'] = {"label": "MRP"}
PRODUCT_FIELDS['base_rate'] = {"label": "Base Price"}
PRODUCT_FIELDS['cgst'] = {"label": "CGST (%)"}
PRODUCT_FIELDS['sgst'] = {"label": "SGST (%)"}
PRODUCT_FIELDS['igst'] = {"label": "IGST (%)"}
PRODUCT_FIELDS['hsn_code'] = {"label": "HSN CODE"}
