#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from ....visual import wintabbrush
from psychopy.iohub.devices import wintab

class WintabBrushComponent(BaseVisualComponent):
    """
    This component is a Wintab compatible drawing tool.
    """

    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'Wintab.png'
    tooltip = _translate('BWintab Brush: a Wintab drawing tool')

    def __init__(self, exp, parentName, name='WintabBrush',
                 lineColor='$[1,1,1]', lineColorSpace='rgb',
                 lineWidth=1.5, opacity=1,
                 buttonRequired=True,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(WintabBrushComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'WintabBrush'
        self.url = "https://www.psychopy.org/builder/components/brush.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.order.remove("opacity")  # Move opacity to the end
        self.order += [
            "lineWidth", "lineColor", "lineColorSpace", "opacity"  # Appearance tab
        ]

        # params
        msg = _translate("Fill color of this brush")
        self.params['lineColor'] = Param(
            lineColor, valType='color', inputType="color", allowedTypes=[], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=msg,
            label= _translate("Brush color"))

        msg = _translate("Width of the brush's line (always in pixels and limited to 10px max width)")
        self.params['lineWidth'] = Param(
            lineWidth, valType='num', inputType="spin", allowedTypes=[], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=msg,
            label= _translate("Brush size"))

        self.params['lineColorSpace'] = self.params['colorSpace']
        del self.params['colorSpace']

        msg = _translate("The line opacity")
        self.params['opacity'].hint=msg

        msg = _translate("Whether a button needs to be pressed to draw (True/False)")
        self.params['buttonRequired'] = Param(
            buttonRequired, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=msg,
            label= _translate("Press button"))

        # Remove BaseVisual params which are not needed
        del self.params['color']  # because color is defined by lineColor
        del self.params['fillColor']
        del self.params['borderColor']
        del self.params['size']  # because size determined by lineWidth
        del self.params['ori']
        del self.params['pos']
        del self.params['units']  # always in pix

        # Add Wintab parameters
        
    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        inits['depth'] = -self.getPosInRoutine()
        code = (
            "{name} = visual.WintabBrush(win=win, name='{name}',\n"
            "   lineWidth={lineWidth},\n"
            "   lineColor={lineColor},\n"
            "   lineColorSpace={lineColorSpace},\n"
            "   opacity={opacity},\n"
            "   buttonRequired={buttonRequired},\n"
            "   depth={depth}\n"
            ")\n"
            "pen = ioServer.devices.pen \n"
            "if pen.getInterfaceStatus() != \"HW_OK\" : \n"
            "   print(\"Error creating Wintab device:\", pen.getInterfaceStatus()) \n"
            "   print(\"TABLET INIT ERROR:\", pen.getLastInterfaceErrorString()) \n"
            "   return \n"
            "pen.reporting = True \n"
        ).format(**inits)
        
        buff.writeIndentedLines(code)

    def writeInitCodeJS(self, buff):
        # JS code does not use Brush class
        params = getInitVals(self.params)
        params['depth'] = -self.getPosInRoutine()

        code = ("{name} = {{}};\n"
                "get{name} = function() {{\n"
                "  return ( new visual.ShapeStim({{\n"
                "    win: psychoJS.window,\n"
                "    vertices: [[0, 0]],\n"
                "    lineWidth: {lineWidth},\n"
                "    lineColor: new util.Color({lineColor}),\n"
                "    opacity: {opacity},\n"
                "    closeShape: false,\n"
                "    autoLog: false,\n"
                "    depth: {depth}\n"
                "    }}))\n"
                "}}\n\n").format(**params)

        buff.writeIndentedLines(code)
        # add reset function
        code = ("{name}Reset = {name}.reset = function() {{\n"
                "  if ({name}Shapes.length > 0) {{\n"
                "    for (let shape of {name}Shapes) {{\n"
                "      shape.setAutoDraw(false);\n"
                "    }}\n"
                "  }}\n"
                "  {name}AtStartPoint = false;\n"
                "  {name}Shapes = [];\n"
                "  {name}CurrentShape = -1;\n"
                "}}\n\n").format(name=params['name'])
        buff.writeIndentedLines(code)

        # Define vars for drawing
        code = ("{name}CurrentShape = -1;\n"
                "{name}BrushPos = [];\n"
                "{name}Pointer = new core.Mouse({{win: psychoJS.window}});\n"
                "{name}AtStartPoint = false;\n"
                "{name}Shapes = [];\n").format(name=params['name'])
        buff.writeIndentedLines(code)

    def writeRoutineStartCode(self, buff):
        # Write the code that will be called at the start of the routine
        super(WintabBrushComponent, self).writeRoutineStartCode(buff)
        code = ("")
        # Reset shapes for each trial
        buff.writeIndented("{}.reset()\n".format(self.params['name']))

    def writeRoutineStartCodeJS(self, buff):
        # Write the code that will be called at the start of the routine
        # super(BrushComponent, self).writeRoutineStartCodeJS(buff)
        # Reset shapes for each trial
        buff.writeIndented("{}Reset();\n".format(self.params['name']))

    def writeFrameCode(self, buff):
        # Write the code that will be called every frame
        code = ("wtab_evts = pen.getSamples() \n"
                "last_evt_count = len(wtab_evts) \n"
                "if last_evt_count: \n"
                "   # for e in wtab_evts: \n"
                "   #    print e \n"
                "   last_evt = wtab_evts[-1] \n"
                "   {name}.updateFromEvents(wtab_evts) \n"
                "   penPosX = last_evt.dict['x'] \n"
                "   penPosY = last_evt.dict['y'] \n"
                "   penPressure = last_evt.dict['pressure'] \n"
                "   penSample = f'x: {{penPosX}}, y: {{penPosY}}, pressure: {{penPressure}}' \n"
                "   print(penSample) \n"
                "{name}.draw()").format(name=self.params['name'])
        buff.writeIndented(code)


    def writeFrameCodeJS(self, buff):
        code = ("if ({name}Pointer.getPressed()[0] === 1 && {name}AtStartPoint != true) {{\n"
                "  {name}AtStartPoint = true;\n"
                "  {name}BrushPos = [];\n"
                "  {name}Shapes.push(get{name}());\n"
                "  {name}CurrentShape += 1;\n"
                "  {name}Shapes[{name}CurrentShape].setAutoDraw(true);\n"
                "}}\n"
                "if ({name}Pointer.getPressed()[0] === 1) {{\n"
                "  {name}BrushPos.push({name}Pointer.getPos());\n"
                "  {name}Shapes[{name}CurrentShape].setVertices({name}BrushPos);\n"
                "}} else {{\n"
                "  {name}AtStartPoint = false;\n"
                "}}\n".format(name=self.params['name']))
        buff.writeIndentedLines(code)
