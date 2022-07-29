from collections import OrderedDict

#=========================================================================
# Csv file fields dictonary
#=========================================================================

SHAKTI_BONUS_FIELDS = OrderedDict()
SHAKTI_BONUS_FIELDS['shakti'] = {"label": "Shakti Code"}
SHAKTI_BONUS_FIELDS['start'] = {"label": "Start Date (mm/dd/yyyy)"}
SHAKTI_BONUS_FIELDS['end'] = {"label": "Expires on (mm/dd/yyyy)"}
SHAKTI_BONUS_FIELDS['target_amount1'] = {"label": "Target Amount 1"}
SHAKTI_BONUS_FIELDS['discount1'] = {"label": "Discount 1"}
SHAKTI_BONUS_FIELDS['target_amount2'] = {"label": "Target Amount 2"}
SHAKTI_BONUS_FIELDS['discount2'] = {"label": "Discount 2"}
SHAKTI_BONUS_FIELDS['target_amount3'] = {"label": "Target Amount 3"}
SHAKTI_BONUS_FIELDS['discount3'] = {"label": "Discount 3"}

TRADE_OFFERS_FIELDS = OrderedDict()
TRADE_OFFERS_FIELDS["promotion__name"] = {"label": "Promotion Name"}
TRADE_OFFERS_FIELDS["promotion__start"] = {"label": "Start Date (mm/dd/yyyy)"}
TRADE_OFFERS_FIELDS["promotion__end"] = {"label": "End Date (mm/dd/yyyy)"}
TRADE_OFFERS_FIELDS["buy_product__basepack_code"] = {"label": "Basepack Code"}
TRADE_OFFERS_FIELDS["buy_quantity"] = {"label": "Buy Quantity"}
TRADE_OFFERS_FIELDS["discount"] = {"label": "Discount"}


SHAKTI_PROMOTION_FIELDS = OrderedDict()
SHAKTI_PROMOTION_FIELDS['name'] = {"label": "Promotion Name"}
SHAKTI_PROMOTION_FIELDS['shakti'] = {"label": "Shakti Code"}
SHAKTI_PROMOTION_FIELDS['start'] = {"label": "Start Date (mm/dd/yyyy)"}
SHAKTI_PROMOTION_FIELDS['end'] = {"label": "Expires on (mm/dd/yyyy)"}
SHAKTI_PROMOTION_FIELDS["basepack_code"] = {
    "label": "Basepack Code"}
SHAKTI_PROMOTION_FIELDS["buy_quantity"] = {"label": "Buy Quantity"}
SHAKTI_PROMOTION_FIELDS["discount"] = {"label": "Discount"}
