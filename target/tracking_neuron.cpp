
/*
 *  tracking_neuron.cpp
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
 *  Generated from NESTML 8.2.0 at time: 2025-11-07 10:59:43.103174
**/

// C++ includes:
#include <limits>

// Includes from libnestutil:
#include "numerics.h"

// Includes from nestkernel:
#include "exceptions.h"
#include "kernel_manager.h"
#include "nest_impl.h"
#include "universal_data_logger_impl.h"

// Includes from sli:
#include "dict.h"
#include "dictutils.h"
#include "doubledatum.h"
#include "integerdatum.h"
#include "lockptrdatum.h"

#include "tracking_neuron.h"

// uncomment the next line to enable printing of detailed debug information
// #define DEBUG
void
register_tracking_neuron( const std::string& name )
{
  nest::register_node_model< tracking_neuron >( name );
}

// ---------------------------------------------------------------------------
//   Recordables map
// ---------------------------------------------------------------------------
nest::RecordablesMap<tracking_neuron> tracking_neuron::recordablesMap_;
namespace nest
{

  // Override the create() method with one call to RecordablesMap::insert_()
  // for each quantity to be recorded.
template <> void RecordablesMap<tracking_neuron>::create()
  {
    // add state variables to recordables map
   insert_(tracking_neuron_names::_out_rate, &tracking_neuron::get_out_rate);
   insert_(tracking_neuron_names::_lambda, &tracking_neuron::get_lambda);
   insert_(tracking_neuron_names::_curr_traj, &tracking_neuron::get_curr_traj);

    // Add vector variables  
  }
}
std::vector< std::tuple< int, int > > tracking_neuron::rport_to_nestml_buffer_idx =
{
  
  { tracking_neuron::EXC_SPIKES, tracking_neuron::INH_SPIKES },
  { tracking_neuron::SPIKES, tracking_neuron::PORT_NOT_AVAILABLE },
};

// ---------------------------------------------------------------------------
//   Default constructors defining default parameters and state
//   Note: the implementation is empty. The initialization is of variables
//   is a part of tracking_neuron's constructor.
// ---------------------------------------------------------------------------

tracking_neuron::Parameters_::Parameters_()
{
}

tracking_neuron::State_::State_()
{
}

// ---------------------------------------------------------------------------
//   Parameter and state extractions and manipulation functions
// ---------------------------------------------------------------------------

tracking_neuron::Buffers_::Buffers_(tracking_neuron &n):
  logger_(n)
  , spike_inputs_( std::vector< nest::RingBuffer >( NUM_SPIKE_RECEPTORS ) )
  , spike_inputs_grid_sum_( std::vector< double >( NUM_SPIKE_RECEPTORS ) )
  , spike_input_received_( std::vector< nest::RingBuffer >( NUM_SPIKE_RECEPTORS ) )
  , spike_input_received_grid_sum_( std::vector< double >( NUM_SPIKE_RECEPTORS ) )
{
  // Initialization of the remaining members is deferred to init_buffers_().
}

tracking_neuron::Buffers_::Buffers_(const Buffers_ &, tracking_neuron &n):
  logger_(n)
  , spike_inputs_( std::vector< nest::RingBuffer >( NUM_SPIKE_RECEPTORS ) )
  , spike_inputs_grid_sum_( std::vector< double >( NUM_SPIKE_RECEPTORS ) )
  , spike_input_received_( std::vector< nest::RingBuffer >( NUM_SPIKE_RECEPTORS ) )
  , spike_input_received_grid_sum_( std::vector< double >( NUM_SPIKE_RECEPTORS ) )
{
  // Initialization of the remaining members is deferred to init_buffers_().
}

// ---------------------------------------------------------------------------
//   Default constructor for node
// ---------------------------------------------------------------------------

tracking_neuron::tracking_neuron():ArchivingNode(), P_(), S_(), B_(*this)
{
  init_state_internal_();
  recordablesMap_.create();
  pre_run_hook();
}

// ---------------------------------------------------------------------------
//   Copy constructor for node
// ---------------------------------------------------------------------------

tracking_neuron::tracking_neuron(const tracking_neuron& __n):
  ArchivingNode(), P_(__n.P_), S_(__n.S_), B_(__n.B_, *this)
{
  // copy parameter struct P_
  P_.kp = __n.P_.kp;
  P_.pos = __n.P_.pos;
  P_.base_rate = __n.P_.base_rate;
  P_.simulation_steps = __n.P_.simulation_steps;
  P_.traj = __n.P_.traj;

  // copy state struct S_
  S_.out_rate = __n.S_.out_rate;
  S_.lambda = __n.S_.lambda;
  S_.spike_count_out = __n.S_.spike_count_out;
  S_.current_step = __n.S_.current_step;
  S_.curr_traj = __n.S_.curr_traj;

  // copy internals V_
  V_.__h = __n.V_.__h;
}

// ---------------------------------------------------------------------------
//   Destructor for node
// ---------------------------------------------------------------------------

tracking_neuron::~tracking_neuron()
{
}

// ---------------------------------------------------------------------------
//   Node initialization functions
// ---------------------------------------------------------------------------
void tracking_neuron::calibrate_time( const nest::TimeConverter& tc )
{
  LOG( nest::M_WARNING,
    "tracking_neuron",
    "Simulation resolution has changed. Internal state and parameters of the model have been reset!" );

  init_state_internal_();
}
void tracking_neuron::init_state_internal_()
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] tracking_neuron::init_state_internal_()" << std::endl;
#endif

  const double __timestep = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the timestep() function
  // initial values for parameters
  P_.kp = 1; // as real
  P_.pos = true; // as boolean
  P_.base_rate = 0; // as real
  P_.simulation_steps = 100; // as integer
  P_.traj.resize(
  P_.simulation_steps, 10.0);

  V_.__h = nest::Time::get_resolution().get_ms();
  recompute_internal_variables();
  // initial values for state variables
  S_.out_rate = 0.0; // as real
  S_.lambda = 0.0; // as real
  S_.spike_count_out = 0; // as integer
  S_.current_step = 0; // as integer
  S_.curr_traj = 0.0; // as real
}

void tracking_neuron::init_buffers_()
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] tracking_neuron::init_buffers_()" << std::endl;
#endif
  // spike input buffers
  get_spike_inputs_().clear();
  get_spike_inputs_grid_sum_().clear();
  get_spike_input_received_().clear();
  get_spike_input_received_grid_sum_().clear();

  B_.logger_.reset();


}

void tracking_neuron::recompute_internal_variables(bool exclude_timestep)
{
  const double __timestep = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the timestep() function

  if (exclude_timestep)
  {    
  }
  else {    
    V_.__h = nest::Time::get_resolution().get_ms(); // as ms
  }
}
void tracking_neuron::pre_run_hook()
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] tracking_neuron::pre_run_hook()" << std::endl;
#endif

  B_.logger_.init();

  // parameters might have changed -- recompute internals
  V_.__h = nest::Time::get_resolution().get_ms();
  recompute_internal_variables();

  // buffers B_
  B_.spike_inputs_.resize(NUM_SPIKE_RECEPTORS);
  B_.spike_inputs_grid_sum_.resize(NUM_SPIKE_RECEPTORS);
  B_.spike_input_received_.resize(NUM_SPIKE_RECEPTORS);
  B_.spike_input_received_grid_sum_.resize(NUM_SPIKE_RECEPTORS);
}

// ---------------------------------------------------------------------------
//   Update and spike handling functions
// ---------------------------------------------------------------------------


void tracking_neuron::update(nest::Time const & origin, const long from, const long to)
{
  const double __timestep = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the timestep() function

  for ( long lag = from ; lag < to ; ++lag )
  {


    auto get_t = [origin, lag](){ return nest::Time( nest::Time::step( origin.get_steps() + lag + 1) ).get_ms(); };

#ifdef DEBUG
    std::cout << "[neuron " << this << "] tracking_neuron::update: handling post spike at t = " << get_t() << std::endl;
#endif
    /**
     * buffer spikes from spiking input ports
    **/

    for (long i = 0; i < NUM_SPIKE_RECEPTORS; ++i)
    {
      get_spike_inputs_grid_sum_()[i] = get_spike_inputs_()[i].get_value(lag);
      get_spike_input_received_grid_sum_()[i] = get_spike_input_received_()[i].get_value(lag);
    }

    /**
     * subthreshold updates of the convolution variables
     *
     * step 1: regardless of whether and how integrate_odes() will be called, update variables due to convolutions
    **/



    /**
     * Begin NESTML generated code for the update block(s)
    **/

  S_.current_step = nest::Time(nest::Time::ms((double) (get_t()))).get_steps();
  S_.curr_traj = P_.traj[S_.current_step];
  if ((((P_.pos == true) && (S_.curr_traj < 0)) || ((P_.pos == false) && (S_.curr_traj) > 0)))
  {  
    S_.curr_traj = 0;
  }
  S_.out_rate = P_.base_rate + P_.kp * std::abs(S_.curr_traj);
  S_.lambda = S_.out_rate * nest::Time::get_resolution().get_ms() * 0.001;
  S_.spike_count_out = ([&]() -> int { nest::poisson_distribution::param_type poisson_params(S_.lambda); int sample = poisson_dev_( nest::get_vp_specific_rng( get_thread() ), poisson_params); return sample; })();
  if (S_.spike_count_out > 0)
  {  

    // begin generated code for emit_spike() function

    #ifdef DEBUG
    std::cout << "Emitting a spike at t = " << nest::Time(nest::Time::step(origin.get_steps() + lag + 1)).get_ms() << "\n";
    #endif
    set_spiketime(nest::Time::step(origin.get_steps() + lag + 1));
    nest::SpikeEvent se;
    nest::kernel().event_delivery_manager.send(*this, se, lag);
    // end generated code for emit_spike() function
  }

    /**
     * Begin NESTML generated code for the onReceive block(s)
    **/


    /**
     * subthreshold updates of the convolution variables
     *
     * step 2: regardless of whether and how integrate_odes() was called, update variables due to convolutions. Set to the updated values at the end of the timestep.
    **/


    /**
     * spike updates due to convolutions
    **/


    /**
     * Begin NESTML generated code for the onCondition block(s)
    **/


    /**
     * handle continuous input ports
    **/
    // voltage logging
    B_.logger_.record_data(origin.get_steps() + lag);
  }
}

// Do not move this function as inline to h-file. It depends on
// universal_data_logger_impl.h being included here.
void tracking_neuron::handle(nest::DataLoggingRequest& e)
{
  B_.logger_.handle(e);
}


void tracking_neuron::handle(nest::SpikeEvent &e)
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] tracking_neuron::handle(SpikeEvent)" << std::endl;
#endif

  assert(e.get_delay_steps() > 0);
  assert( e.get_rport() < B_.spike_inputs_.size() );

  double weight = e.get_weight();
  size_t nestml_buffer_idx = 0;
  if ( weight >= 0.0 )
  {
    nestml_buffer_idx = std::get<0>(rport_to_nestml_buffer_idx[e.get_rport()]);
  }
  else
  {
    nestml_buffer_idx = std::get<1>(rport_to_nestml_buffer_idx[e.get_rport()]);
    if ( nestml_buffer_idx == tracking_neuron::PORT_NOT_AVAILABLE )
    {
      nestml_buffer_idx = std::get<0>(rport_to_nestml_buffer_idx[e.get_rport()]);
    }
    weight = -weight;
  }
  B_.spike_inputs_[ nestml_buffer_idx - MIN_SPIKE_RECEPTOR ].add_value(
    e.get_rel_delivery_steps( nest::kernel().simulation_manager.get_slice_origin() ),
    weight * e.get_multiplicity() );
  B_.spike_input_received_[ nestml_buffer_idx - MIN_SPIKE_RECEPTOR ].add_value(
    e.get_rel_delivery_steps( nest::kernel().simulation_manager.get_slice_origin() ),
    1. );
}

// -------------------------------------------------------------------------
//   Methods corresponding to event handlers
// -------------------------------------------------------------------------

