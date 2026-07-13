
/*
*  nestml_allmodels_module.cpp
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
*  2024-11-05 14:48:37.050316
*/

// Include from NEST
#include "nest_extension_interface.h"

// include headers with your own stuff

#include "tracking_neuron_nestml.h"
#include "controller_neurons_module.h"
#include  "basic_neuron_nestml.h"
#include  "diff_neuron_nestml.h"
#include  "rb_neuron_nestml.h"
#include  "tracking_neuron_planner_nestml.h"
#include "state_neuron_nestml.h"


class controller_neurons_module : public nest::NESTExtensionInterface
{
  public:
    controller_neurons_module() {}
    ~controller_neurons_module() {}

    void initialize() override;
};

// Define module instance outside of namespace to avoid name-mangling problems
controller_neurons_module controller_neurons_module_LTX_module;

void controller_neurons_module::initialize()
{
    // register neurons, synapse or device models
    register_tracking_neuron_nestml("tracking_neuron_nestml");

    register_basic_neuron_nestml("basic_neuron_nestml");
    register_diff_neuron_nestml("diff_neuron_nestml");/*  */

    register_rb_neuron_nestml("rb_neuron_nestml");
    register_tracking_neuron_planner_nestml("tracking_neuron_planner_nestml");
    register_state_neuron_nestml("state_neuron_nestml");



    

}
