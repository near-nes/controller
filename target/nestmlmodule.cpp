
/*
*  nestmlmodule.cpp
*
*  This file is part of NEST.
*
*  Copyright (C) 2004 The NEST Initiative
*
*  NEST is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 2 of the License, or
*  (at your option) any later version.
*
*  NEST is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
*
*  Generated from NESTML 8.2.0 at time: 2025-11-07 11:02:04.762684
*/

// Include from NEST
#include "nest_extension_interface.h"

// include headers with your own stuff


#include "state_neuron.h"



class nestmlmodule : public nest::NESTExtensionInterface
{
  public:
    nestmlmodule() {}
    ~nestmlmodule() {}

    void initialize() override;
};

nestmlmodule nestmlmodule_LTX_module;

void nestmlmodule::initialize()
{
    // register neurons
    register_state_neuron("state_neuron");
}
