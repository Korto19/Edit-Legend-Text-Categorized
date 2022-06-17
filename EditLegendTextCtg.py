# -*-coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   Giulio Fattori aka Korto19 - 15.06.2022                                             *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsExpression,
                       QgsExpressionContext,
                       QgsExpressionContextUtils,
                       QgsCategorizedSymbolRenderer,
                       QgsRendererCategory,
                       QgsMarkerSymbol,
                       QgsLineSymbol,
                       QgsFillSymbol,
                       QgsFeatureSink,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsProject,
                       QgsVectorLayer,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDefinition,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProcessingParameterFileDestination
                       )
import processing

#code for processing icon
#import os
#import inspect
from qgis.PyQt.QtGui import QIcon
#cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

class EditLegendTextCtg_ProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm that fractions a poligon in n parts.
    """
    INPUT        = 'INPUT'         #layer
    INPUT_NEW    = 'INPUT_NEW'     #campo nuova legenda

    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return EditLegendTextCtg_ProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Edit Legend Text Ctg'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Edit Legend Text Ctg')
        
    #processing icon
    def icon(self):
        #cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(":images/themes/default/legend.svg")
        return icon

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        
        header = '''
                    <img src=":images/themes/default/legend.svg" width="50" height="50" style="float:right">
        '''
        
        return self.tr(header + "Modifica la legenda di un layer categorizzato in base ad un altro campo<p>\
            <ul><li><strong><mark style='color:blue'>riconosce le categorizzazione con espressione</strong></li>\
            <li><strong><mark style='color:blue'>modifica solo il testo descrittivo</strong></li>\
            <li><strong><mark style='color:blue'>versione minima QGIS 3.24</strong></li></ul>\
            <strong><mark style='color:blue'></strong>\
            ")
    
    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # We add the point input vector features source
        #QgsProcessingFeatureSourceDefinition 
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Layer categorizzato'),
                [QgsProcessing.TypeMapLayer]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_NEW,
                'Attributo da inserire',
                #defaultValue = 'nomePDF',
                parentLayerParameterName=self.INPUT
            )
        )
    
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        source = self.parameterAsLayer(
            parameters,
            self.INPUT,
            context)
                   
        field_new_descr = self.parameterAsString(
            parameters,
            self.INPUT_NEW,
            context)
      
        #verifico che sia categorizzato e recupero campo di classificazione
        if source.renderer().type() == "categorizedSymbol":
            field_class = source.renderer().legendClassificationAttribute()
            field_expression = QgsExpression(field_class)
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(source))
            #print(field_class)

            #recupero i valori da inserire dal campo specificato
            new_label ={}
            for feature in source.getFeatures():
                context.setFeature(feature)
                exp_val = field_expression.evaluate(context)
                new_label[exp_val] = feature[field_new_descr]
            new_label['NULL'] = 'NULL'
            #print(new_label)
            
            #recupero le categorie esistenti
            categories = source.renderer().categories()
            
            #creo nuove categorie e lista categorie
            new_category = QgsRendererCategory()
            new_categories = []
            
            new_sym = QgsFillSymbol()
            
            #ciclo sulle categorie esistenti
            for i, category in enumerate(categories):
                #copio il simbolo esistente
                new_sym = category.symbol()
                
                #creo la nuova categoria senza cambiare simbolo ma modificando etichetta
                if i < len(categories)-1:
                    #print(category.value(), new_sym.clone(), str(new_label[category.value()]) )
                    etichetta = str(new_label[category.value()])
                else:
                    #print(i, category.value(), new_sym.clone())
                    etichetta = ""
                
                new_categories.append(QgsRendererCategory(category.value(), new_sym.clone(), etichetta))

            #applico la tematizzazione
            new_renderer = QgsCategorizedSymbolRenderer(field_class, new_categories)

            source.setRenderer(new_renderer)
            source.triggerRepaint()
        
        else:
            feedback.reportError('Layer non categorizzato')
        
        return {}