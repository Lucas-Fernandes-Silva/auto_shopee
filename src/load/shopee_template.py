import os

import pandas as pd

arquivo = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_upseller.xlsx"
upseller = pd.read_excel(arquivo)
produtos = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/final_com_imagens.xlsx")
upseller_colunas = upseller.columns.tolist()

teste = produtos[503:506]
produtos = teste.copy()

def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    mapa = {
        'ps_category|0|0': "101197",
        'ps_product_name|1|0': item.get("Base",""),
        'ps_product_description|1|0': item.get("Descrição",""),
        'ps_sku_parent_short|0|0': item.get("ID_Variacao",""),
        'et_title_variation_integration_no|0|0': item.get("",""),
        'et_title_variation_1|0|0': item.get("",""),
        'et_title_option_for_variation_1|0|0': item.get("",""),
        'et_title_image_per_variation|0|3': item.get("",""),
        'et_title_variation_2|0|0': item.get("",""),
        'et_title_option_for_variation_2|0|0': item.get("",""),
        'ps_price|1|1': item.get("",""),
        'ps_stock|0|1': item.get("",""),
        'ps_sku_short|0|0': item.get("",""),
        'ps_new_size_chart|0|1': item.get("",""),
        'et_title_size_chart|0|3': item.get("",""),
        'ps_gtin_code|0|0': item.get("",""),
        'sl_tool_mass_upload_compatibility_title|0|0': item.get("",""),
        'ps_item_cover_image|0|3': item.get("",""),
        'ps_item_image_1|0|3': item.get("",""),
        'ps_item_image_2|0|3': item.get("",""),
        'ps_item_image_3|0|3': item.get("",""),
        'ps_item_image_4|0|3': item.get("",""),
        'ps_item_image_5|0|3': item.get("",""),
        'ps_item_image_6|0|3': item.get("",""),
        'ps_item_image_7|0|3': item.get("",""),
        'ps_item_image_8|0|3': item.get("",""),
        'ps_weight|1|1': item.get("",""),
        'ps_length|0|1': item.get("",""),
        'ps_width|0|1': item.get("",""),
        'ps_height|0|1': item.get("",""),
        'channel_id.90016|0|0': item.get("",""),
        'channel_id.90023|0|0': item.get("",""),
        'ps_product_pre_order_dts|0|1': item.get("",""),
        'ps_invoice_ncm|0|0': item.get("",""),
        'ps_invoice_cfop_same|0|0': item.get("",""),
        'ps_invoice_cfop_diff|0|0': item.get("",""),
        'ps_invoice_origin|0|0': item.get("",""),
        'ps_invoice_csosn|0|0': item.get("",""),
        'ps_invoice_cest|0|0': item.get("",""),
        'ps_invoice_measure_unit|0|0': item.get("",""),
        'ps_pis_cofins_cst_default|0|0': item.get("",""),
        'ps_federal_state_taxes_default|0|0': item.get("",""),
        'ps_operation_type_default|0|0': item.get("",""),
        'ps_ex_tipi_default|0|0': item.get("",""),
        'ps_fci_num_default|0|0': item.get("",""),
        'ps_recopi_num_default|0|0': item.get("",""),
        'ps_additional_info_default|0|0': item.get("",""),
        'sl_label_product_is_grouped_item|0|0': item.get("",""),
        'sl_label_grouped_item_gtin_sscc|0|0': item.get("",""),
        'sl_label_grouped_item_qty|0|0': item.get("",""),
        'sl_label_grouped_item_measure_unity|0|0': item.get("",""),
        'et_title_reason|0|0': item.get("","")
    }

    linha.update(mapa)
    return linha


linhas_bling = [criar_linha(row, upseller_colunas) for _, row in produtos.iterrows()]
bling_df = pd.DataFrame(linhas_bling, columns=upseller_colunas)

bling_df["Peso (kg)*"] = bling_df["Peso (kg)*"].fillna(1)

if os.path.exists(arquivo):
    df_existente = pd.read_excel(arquivo)
    df_final = pd.concat([df_existente, bling_df], ignore_index=True)
else:
    df_final = bling_df


# Salva tudo de novo (mantém todas as linhas)
df_final.to_excel("shopee.xlsx", index=False)
