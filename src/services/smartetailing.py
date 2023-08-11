from typing import Dict, List, Union

from utils.xml import escape_special_characters


def create_xml(products: List[str]):
    return f'''<?xml version="1.0" encoding="UTF-8"?><Products xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">{''.join(products)}</Products>'''


def create_product_xml_element(
        sku: Union[str, None],
        brand: Union[str, None],
        model: Union[str, None],
        year: Union[str, None],
        description: Union[str, None],
        genders: Union[List[str], None],
        msrp: Union[float, str, None],
        gtin: Union[float, str, None],
        length: Union[float, str, None],
        width: Union[float, str, None],
        height: Union[float, str, None],
        weight: Union[float, str, None],
        images: Union[List[str], None],
        default_image: Union[str, None],
        categories: Union[List[str], None],
        spec_items: Union[List[Dict[str, str]], None],):
    if sku is None: sku = ''
    if msrp is None: msrp = ''
    if gtin is None: gtin = ''
    if length is None: length = ''
    if width is None: width = ''
    if height is None: height = ''
    if weight is None: weight = ''
    if default_image is None: default_image = ''
    brand = escape_special_characters(brand)
    model = escape_special_characters(model)
    description = escape_special_characters(description)
    return f'''<Product><modelSku>{sku}</modelSku><modelName>{model}</modelName><modelYear>{year}</modelYear><modelDescription><![CDATA[{description}]]></modelDescription><gender>{get_gender(genders=genders)}</gender><Brand><name>{brand}</name></Brand><Specs>{create_specs_xml_element(spec_items=spec_items)}</Specs><Categories>{create_categories_xml_element(categories=categories)}</Categories><ModelImages>{create_images_xml_element(images=images)}</ModelImages><VariationCombinations><VariationCombination><mpn/><gtin1>{gtin}</gtin1><msrp>{msrp}</msrp><length>{length}</length><width>{width}</width><height>{height}</height><weight>{weight}</weight></VariationCombination></VariationCombinations><bbb><DefaultImage>{default_image}</DefaultImage></bbb></Product>'''


def get_gender(genders: Union[List[str], None]):
    if genders is not None:
        genders_have = lambda gender: gender in genders
        if genders_have('Boys') or genders_have('Girls'): return 'Kids'
        if genders_have('Unisex') or (genders_have('Men') and genders_have('Women')): return 'Unisex'
        if genders_have('Men'): return 'Men\'s'
        if genders_have('Women'): return 'Women\'s'
    return 'Not Designated'


def create_spec_xml_element(spec_name: str, spec_value: str):
    spec_name = escape_special_characters(spec_name)
    spec_value = escape_special_characters(spec_value)
    return f'''<Spec><name>{spec_name}</name><value>{spec_value}</value></Spec>'''


def create_specs_xml_element(spec_items: Union[List[Dict[str, str]], None]):
    if spec_items is None: return ''
    return ''.join([create_spec_xml_element(spec_name=spec['name'], spec_value=spec['value']) for spec in spec_items])


def create_image_xml_element(image: str, order = 0):
    image = escape_special_characters(image)
    return f'''<ModelImage><micro url="{image}">{image}</micro><small url="{image}">{image}</small><large url="{image}">{image}</large><zoom url="{image}">{image}</zoom><sortOrder>{order}</sortOrder></ModelImage>'''


def create_images_xml_element(images: Union[List[str], None]):
    if images is None: return ''
    return ''.join([create_image_xml_element(image=images[index], order=index) for index in range(len(images))])


def create_category_xml_element(category: str):
    category_id = 0
    category_name = escape_special_characters(category)
    return f'''<Category><ID>{category_id}</ID><name>{category_name}</name></Category>'''


def create_categories_xml_element(categories: Union[List[str], None]):
    if categories is None: return ''
    return ''.join([create_category_xml_element(category=category) for category in categories])