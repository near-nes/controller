
/*
 *  state_neuron.cpp
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
 *  Generated from NESTML 8.2.0 at time: 2025-11-30 15:35:07.938415
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

#include "state_neuron.h"

// uncomment the next line to enable printing of detailed debug information
// #define DEBUG
void
register_state_neuron( const std::string& name )
{
  nest::register_node_model< state_neuron >( name );
}

// ---------------------------------------------------------------------------
//   Recordables map
// ---------------------------------------------------------------------------
namespace nest
{

  // Override the create() method with one call to RecordablesMap::insert_()
  // for each quantity to be recorded.
template <> void DynamicRecordablesMap<state_neuron>::create(state_neuron& host)
  {
    insert("in_rate", host.get_data_access_functor( state_neuron::State_::IN_RATE ));
    insert("out_rate", host.get_data_access_functor( state_neuron::State_::OUT_RATE ));
    insert("mean_fbk", host.get_data_access_functor( state_neuron::State_::MEAN_FBK ));
    insert("mean_pred", host.get_data_access_functor( state_neuron::State_::MEAN_PRED ));
    insert("var_fbk", host.get_data_access_functor( state_neuron::State_::VAR_FBK ));
    insert("var_pred", host.get_data_access_functor( state_neuron::State_::VAR_PRED ));
    insert("CV_fbk", host.get_data_access_functor( state_neuron::State_::CV_FBK ));
    insert("CV_pred", host.get_data_access_functor( state_neuron::State_::CV_PRED ));
    insert("current_error_input", host.get_data_access_functor( state_neuron::State_::CURRENT_ERROR_INPUT ));
    insert("error_counts", host.get_data_access_functor( state_neuron::State_::ERROR_COUNTS ));
    insert("error_rate", host.get_data_access_functor( state_neuron::State_::ERROR_RATE ));
    insert("fbk_rate", host.get_data_access_functor( state_neuron::State_::FBK_RATE ));
    insert("w_fbk", host.get_data_access_functor( state_neuron::State_::W_FBK ));
    insert("w_pred", host.get_data_access_functor( state_neuron::State_::W_PRED ));
    insert("total_CV", host.get_data_access_functor( state_neuron::State_::TOTAL_CV ));
    insert("lambda_poisson", host.get_data_access_functor( state_neuron::State_::LAMBDA_POISSON ));

    // Add vector variables  
      host.insert_recordables();
  }
}
std::vector< std::tuple< int, int > > state_neuron::rport_to_nestml_buffer_idx =
{
  { state_neuron::FBK_SPIKES_0, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_1, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_2, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_3, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_4, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_5, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_6, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_7, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_8, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_9, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_10, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_11, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_12, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_13, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_14, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_15, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_16, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_17, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_18, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_19, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_20, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_21, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_22, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_23, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_24, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_25, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_26, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_27, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_28, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_29, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_30, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_31, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_32, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_33, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_34, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_35, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_36, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_37, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_38, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_39, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_40, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_41, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_42, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_43, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_44, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_45, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_46, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_47, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_48, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_49, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_50, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_51, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_52, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_53, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_54, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_55, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_56, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_57, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_58, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_59, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_60, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_61, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_62, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_63, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_64, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_65, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_66, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_67, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_68, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_69, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_70, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_71, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_72, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_73, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_74, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_75, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_76, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_77, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_78, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_79, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_80, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_81, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_82, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_83, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_84, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_85, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_86, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_87, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_88, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_89, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_90, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_91, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_92, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_93, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_94, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_95, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_96, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_97, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_98, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_99, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_100, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_101, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_102, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_103, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_104, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_105, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_106, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_107, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_108, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_109, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_110, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_111, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_112, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_113, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_114, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_115, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_116, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_117, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_118, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_119, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_120, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_121, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_122, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_123, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_124, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_125, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_126, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_127, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_128, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_129, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_130, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_131, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_132, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_133, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_134, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_135, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_136, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_137, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_138, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_139, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_140, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_141, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_142, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_143, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_144, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_145, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_146, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_147, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_148, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_149, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_150, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_151, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_152, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_153, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_154, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_155, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_156, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_157, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_158, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_159, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_160, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_161, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_162, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_163, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_164, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_165, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_166, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_167, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_168, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_169, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_170, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_171, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_172, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_173, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_174, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_175, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_176, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_177, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_178, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_179, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_180, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_181, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_182, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_183, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_184, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_185, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_186, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_187, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_188, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_189, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_190, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_191, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_192, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_193, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_194, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_195, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_196, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_197, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_198, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::FBK_SPIKES_199, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_0, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_1, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_2, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_3, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_4, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_5, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_6, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_7, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_8, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_9, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_10, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_11, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_12, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_13, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_14, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_15, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_16, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_17, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_18, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_19, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_20, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_21, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_22, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_23, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_24, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_25, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_26, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_27, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_28, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_29, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_30, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_31, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_32, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_33, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_34, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_35, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_36, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_37, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_38, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_39, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_40, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_41, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_42, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_43, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_44, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_45, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_46, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_47, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_48, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_49, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_50, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_51, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_52, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_53, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_54, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_55, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_56, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_57, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_58, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_59, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_60, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_61, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_62, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_63, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_64, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_65, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_66, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_67, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_68, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_69, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_70, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_71, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_72, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_73, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_74, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_75, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_76, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_77, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_78, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_79, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_80, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_81, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_82, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_83, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_84, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_85, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_86, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_87, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_88, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_89, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_90, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_91, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_92, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_93, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_94, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_95, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_96, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_97, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_98, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_99, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_100, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_101, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_102, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_103, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_104, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_105, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_106, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_107, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_108, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_109, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_110, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_111, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_112, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_113, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_114, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_115, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_116, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_117, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_118, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_119, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_120, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_121, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_122, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_123, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_124, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_125, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_126, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_127, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_128, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_129, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_130, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_131, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_132, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_133, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_134, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_135, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_136, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_137, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_138, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_139, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_140, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_141, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_142, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_143, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_144, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_145, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_146, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_147, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_148, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_149, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_150, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_151, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_152, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_153, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_154, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_155, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_156, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_157, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_158, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_159, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_160, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_161, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_162, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_163, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_164, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_165, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_166, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_167, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_168, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_169, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_170, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_171, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_172, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_173, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_174, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_175, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_176, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_177, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_178, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_179, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_180, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_181, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_182, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_183, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_184, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_185, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_186, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_187, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_188, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_189, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_190, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_191, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_192, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_193, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_194, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_195, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_196, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_197, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_198, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::PRED_SPIKES_199, state_neuron::PORT_NOT_AVAILABLE },
  { state_neuron::ERROR_SPIKES, state_neuron::PORT_NOT_AVAILABLE },
};
  std::string state_neuron::get_var_name(size_t elem, std::string var_name)
  {
    std::stringstream n;
    n << var_name << elem;
    return n.str();
  }

  void state_neuron::insert_recordables(size_t first)
  {
      for (size_t i = 0; i < 
P_.N_fbk; i++)
      {
        size_t elem = state_neuron::State_::CURRENT_FBK_INPUT + i;
        recordablesMap_.insert(get_var_name(i, "CURRENT_FBK_INPUT_"), this->get_data_access_functor(elem));
      }
      for (size_t i = 0; i < 
P_.N_pred; i++)
      {
        size_t elem = state_neuron::State_::CURRENT_PRED_INPUT + i;
        recordablesMap_.insert(get_var_name(i, "CURRENT_PRED_INPUT_"), this->get_data_access_functor(elem));
      }
      for (size_t i = 0; i < 
P_.fbk_bf_size; i++)
      {
        size_t elem = state_neuron::State_::FBK_BUFFER + i;
        recordablesMap_.insert(get_var_name(i, "FBK_BUFFER_"), this->get_data_access_functor(elem));
      }
      for (size_t i = 0; i < 
P_.pred_bf_size; i++)
      {
        size_t elem = state_neuron::State_::PRED_BUFFER + i;
        recordablesMap_.insert(get_var_name(i, "PRED_BUFFER_"), this->get_data_access_functor(elem));
      }
      for (size_t i = 0; i < 
P_.N_fbk; i++)
      {
        size_t elem = state_neuron::State_::FBK_COUNTS + i;
        recordablesMap_.insert(get_var_name(i, "FBK_COUNTS_"), this->get_data_access_functor(elem));
      }
      for (size_t i = 0; i < 
P_.N_pred; i++)
      {
        size_t elem = state_neuron::State_::PRED_COUNTS + i;
        recordablesMap_.insert(get_var_name(i, "PRED_COUNTS_"), this->get_data_access_functor(elem));
      }
      for (size_t i = 0; i < 
P_.error_bf_size; i++)
      {
        size_t elem = state_neuron::State_::ERROR_BUFFER + i;
        recordablesMap_.insert(get_var_name(i, "ERROR_BUFFER_"), this->get_data_access_functor(elem));
      }
  }

  nest::DataAccessFunctor< state_neuron >
  state_neuron::get_data_access_functor( size_t elem )
  {
    return nest::DataAccessFunctor< state_neuron >( *this, elem );
  }

// ---------------------------------------------------------------------------
//   Default constructors defining default parameters and state
//   Note: the implementation is empty. The initialization is of variables
//   is a part of state_neuron's constructor.
// ---------------------------------------------------------------------------

state_neuron::Parameters_::Parameters_()
{
}

state_neuron::State_::State_()
{
}

// ---------------------------------------------------------------------------
//   Parameter and state extractions and manipulation functions
// ---------------------------------------------------------------------------

state_neuron::Buffers_::Buffers_(state_neuron &n):
  logger_(n)
  , spike_inputs_( std::vector< nest::RingBuffer >( NUM_SPIKE_RECEPTORS ) )
  , spike_inputs_grid_sum_( std::vector< double >( NUM_SPIKE_RECEPTORS ) )
  , spike_input_received_( std::vector< nest::RingBuffer >( NUM_SPIKE_RECEPTORS ) )
  , spike_input_received_grid_sum_( std::vector< double >( NUM_SPIKE_RECEPTORS ) )
{
  // Initialization of the remaining members is deferred to init_buffers_().
}

state_neuron::Buffers_::Buffers_(const Buffers_ &, state_neuron &n):
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

state_neuron::state_neuron():ArchivingNode(), P_(), S_(), B_(*this)
{
  init_state_internal_();
  recordablesMap_.create(*this);
  pre_run_hook();
}

// ---------------------------------------------------------------------------
//   Copy constructor for node
// ---------------------------------------------------------------------------

state_neuron::state_neuron(const state_neuron& __n):
  ArchivingNode(), P_(__n.P_), S_(__n.S_), B_(__n.B_, *this)
{
  // copy parameter struct P_
  P_.kp = __n.P_.kp;
  P_.pos = __n.P_.pos;
  P_.base_rate = __n.P_.base_rate;
  P_.buffer_size = __n.P_.buffer_size;
  P_.buffer_size_error = __n.P_.buffer_size_error;
  P_.simulation_steps = __n.P_.simulation_steps;
  P_.N_fbk = __n.P_.N_fbk;
  P_.N_pred = __n.P_.N_pred;
  P_.N_error = __n.P_.N_error;
  P_.C_error = __n.P_.C_error;
  P_.fbk_bf_size = __n.P_.fbk_bf_size;
  P_.pred_bf_size = __n.P_.pred_bf_size;
  P_.error_bf_size = __n.P_.error_bf_size;
  P_.time_wait = __n.P_.time_wait;
  P_.time_trial = __n.P_.time_trial;

  // copy state struct S_
  S_.in_rate = __n.S_.in_rate;
  S_.out_rate = __n.S_.out_rate;
  S_.spike_count_out = __n.S_.spike_count_out;
  S_.current_fbk_input = __n.S_.current_fbk_input;
  S_.current_pred_input = __n.S_.current_pred_input;
  S_.fbk_buffer = __n.S_.fbk_buffer;
  S_.pred_buffer = __n.S_.pred_buffer;
  S_.fbk_counts = __n.S_.fbk_counts;
  S_.pred_counts = __n.S_.pred_counts;
  S_.tick = __n.S_.tick;
  S_.position_count = __n.S_.position_count;
  S_.mean_fbk = __n.S_.mean_fbk;
  S_.mean_pred = __n.S_.mean_pred;
  S_.var_fbk = __n.S_.var_fbk;
  S_.var_pred = __n.S_.var_pred;
  S_.CV_fbk = __n.S_.CV_fbk;
  S_.CV_pred = __n.S_.CV_pred;
  S_.current_error_input = __n.S_.current_error_input;
  S_.error_buffer = __n.S_.error_buffer;
  S_.err_pos_count = __n.S_.err_pos_count;
  S_.error_counts = __n.S_.error_counts;
  S_.error_rate = __n.S_.error_rate;
  S_.fbk_rate = __n.S_.fbk_rate;
  S_.w_fbk = __n.S_.w_fbk;
  S_.w_pred = __n.S_.w_pred;
  S_.total_CV = __n.S_.total_CV;
  S_.lambda_poisson = __n.S_.lambda_poisson;

  // copy internals V_
  V_.res = __n.V_.res;
  V_.__h = __n.V_.__h;
  V_.buffer_steps = __n.V_.buffer_steps;
  V_.trial_steps = __n.V_.trial_steps;
  V_.wait_steps = __n.V_.wait_steps;
  V_.buffer_error_steps = __n.V_.buffer_error_steps;
  recordablesMap_.create(*this);
}

// ---------------------------------------------------------------------------
//   Destructor for node
// ---------------------------------------------------------------------------

state_neuron::~state_neuron()
{
}

// ---------------------------------------------------------------------------
//   Node initialization functions
// ---------------------------------------------------------------------------
void state_neuron::calibrate_time( const nest::TimeConverter& tc )
{
  LOG( nest::M_WARNING,
    "state_neuron",
    "Simulation resolution has changed. Internal state and parameters of the model have been reset!" );

  init_state_internal_();
}
void state_neuron::init_state_internal_()
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] state_neuron::init_state_internal_()" << std::endl;
#endif

  const double __timestep = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the timestep() function
  // initial values for parameters
  P_.kp = 1; // as real
  P_.pos = true; // as boolean
  P_.base_rate = 0; // as Hz
  P_.buffer_size = 150.0; // as ms
  P_.buffer_size_error = 25.0; // as ms
  P_.simulation_steps = 1000; // as integer
  P_.N_fbk = 200; // as integer
  P_.N_pred = 200; // as integer
  P_.N_error = 200; // as integer
  P_.C_error = 5.0; // as real
  P_.fbk_bf_size = 30000; // as integer
  P_.pred_bf_size = 30000; // as integer
  P_.error_bf_size = 25; // as integer
  P_.time_wait = 150.0; // as ms
  P_.time_trial = 650.0; // as ms

  V_.__h = nest::Time::get_resolution().get_ms();
  recompute_internal_variables();
  // initial values for state variables
  S_.in_rate = 0; // as Hz
  S_.out_rate = 0; // as Hz
  S_.spike_count_out = 0; // as integer
  S_.current_fbk_input.resize(
  P_.N_fbk, 0);
  S_.current_pred_input.resize(
  P_.N_pred, 0);
  S_.fbk_buffer.resize(
  P_.fbk_bf_size, 0);
  S_.pred_buffer.resize(
  P_.pred_bf_size, 0);
  S_.fbk_counts.resize(
  P_.N_fbk, 0);
  S_.pred_counts.resize(
  P_.N_pred, 0);
  S_.tick = 0; // as integer
  S_.position_count = 0; // as integer
  S_.mean_fbk = 0.0; // as real
  S_.mean_pred = 0.0; // as real
  S_.var_fbk = 0.0; // as real
  S_.var_pred = 0.0; // as real
  S_.CV_fbk = 0.0; // as real
  S_.CV_pred = 0.0; // as real
  S_.current_error_input = 0; // as real
  S_.error_buffer.resize(
  P_.error_bf_size, 0);
  S_.err_pos_count = 0; // as integer
  S_.error_counts = 0.0; // as real
  S_.error_rate = 0.0; // as real
  S_.fbk_rate = 0.0; // as real
  S_.w_fbk = 0.0; // as real
  S_.w_pred = 0.0; // as real
  S_.total_CV = 0.0; // as real
  S_.lambda_poisson = 0; // as real
}

void state_neuron::init_buffers_()
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] state_neuron::init_buffers_()" << std::endl;
#endif
  // spike input buffers
  get_spike_inputs_().clear();
  get_spike_inputs_grid_sum_().clear();
  get_spike_input_received_().clear();
  get_spike_input_received_grid_sum_().clear();

  B_.logger_.reset();


}

void state_neuron::recompute_internal_variables(bool exclude_timestep)
{
  const double __timestep = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the timestep() function

  if (exclude_timestep)
  {    
    V_.res = nest::Time::get_resolution().get_ms(); // as ms
    V_.buffer_steps = nest::Time(nest::Time::ms((double) (P_.buffer_size))).get_steps(); // as integer
    V_.trial_steps = nest::Time(nest::Time::ms((double) (P_.time_trial))).get_steps(); // as integer
    V_.wait_steps = nest::Time(nest::Time::ms((double) (P_.time_wait))).get_steps(); // as integer
    V_.buffer_error_steps = nest::Time(nest::Time::ms((double) (P_.buffer_size_error))).get_steps(); // as integer
  }
  else {    
    V_.res = nest::Time::get_resolution().get_ms(); // as ms
    V_.__h = nest::Time::get_resolution().get_ms(); // as ms
    V_.buffer_steps = nest::Time(nest::Time::ms((double) (P_.buffer_size))).get_steps(); // as integer
    V_.trial_steps = nest::Time(nest::Time::ms((double) (P_.time_trial))).get_steps(); // as integer
    V_.wait_steps = nest::Time(nest::Time::ms((double) (P_.time_wait))).get_steps(); // as integer
    V_.buffer_error_steps = nest::Time(nest::Time::ms((double) (P_.buffer_size_error))).get_steps(); // as integer
  }
}
void state_neuron::pre_run_hook()
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] state_neuron::pre_run_hook()" << std::endl;
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


void state_neuron::update(nest::Time const & origin, const long from, const long to)
{
  const double __timestep = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the timestep() function

  for ( long lag = from ; lag < to ; ++lag )
  {


    auto get_t = [origin, lag](){ return nest::Time( nest::Time::step( origin.get_steps() + lag + 1) ).get_ms(); };

#ifdef DEBUG
    std::cout << "[neuron " << this << "] state_neuron::update: handling post spike at t = " << get_t() << std::endl;
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

  S_.tick = nest::Time(nest::Time::ms((double) (get_t()))).get_steps();
  long i = 0;
  S_.current_error_input = (0.001 * B_.spike_inputs_grid_sum_[ERROR_SPIKES - MIN_SPIKE_RECEPTOR]) / (nest::Time::get_resolution().get_ms() * 0.001);
  for ( i = 0;
                   i<(P_.N_fbk - 1);
       i += 1 )
  {
    S_.current_fbk_input[i] = (0.001 * B_.spike_inputs_grid_sum_[FBK_SPIKES_0 + i - MIN_SPIKE_RECEPTOR]);
  }
  long j = 0;
  for ( j = 0;
                   j<(P_.N_pred - 1);
       j += 1 )
  {
    S_.current_pred_input[j] = (0.001 * B_.spike_inputs_grid_sum_[PRED_SPIKES_0 + j - MIN_SPIKE_RECEPTOR]);
  }
  long index = 0;
  for ( i = 0;
                   i<(P_.N_fbk - 1);
       i += 1 )
  {
    index = S_.position_count * P_.N_fbk + i;
    S_.fbk_buffer[index] = S_.current_fbk_input[i];
  }
  for ( j = 0;
                   j<(P_.N_pred - 1);
       j += 1 )
  {
    index = S_.position_count * P_.N_pred + j;
    S_.pred_buffer[index] = S_.current_pred_input[j];
  }
  S_.position_count += 1;
  if (S_.position_count > V_.buffer_steps - 1)
  {  
    S_.position_count = 0;
  }
  long k = 0;
  long jump = 0;
  for ( k = 0;
                   k<(P_.N_fbk - 1);
       k += 1 )
  {
    S_.fbk_counts[k] = 0;
    for ( jump = 0;
                     jump<(V_.buffer_steps - 1);
         jump += 1 )
    {
      index = P_.N_fbk * jump + k;
      if (S_.fbk_buffer[index] != 0)
      {  
        S_.fbk_counts[k] += 1;
      }
    }
  }
  long m = 0;
  for ( m = 0;
                   m<(P_.N_pred - 1);
       m += 1 )
  {
    S_.pred_counts[m] = 0;
    for ( jump = 0;
                     jump<(V_.buffer_steps - 1);
         jump += 1 )
    {
      index = (P_.N_pred * jump) + m;
      if (S_.pred_buffer[index] != 0)
      {  
        S_.pred_counts[m] += 1;
      }
    }
  }
  S_.mean_fbk = 0.0;
  if (P_.N_fbk == 0)
  {  
    S_.CV_fbk = pow(10, 6);
  }
  else
  {  
    for ( k = 0;
                     k<(P_.N_fbk - 1);
         k += 1 )
    {
      S_.mean_fbk += S_.fbk_counts[k];
    }
    S_.mean_fbk /= P_.N_fbk;
  }
  S_.mean_pred = 0.0;
  if (P_.N_pred == 0)
  {  
    S_.CV_pred = pow(10, 6);
  }
  else
  {  
    for ( m = 0;
                     m<(P_.N_pred - 1);
         m += 1 )
    {
      S_.mean_pred += S_.pred_counts[m];
    }
    S_.mean_pred /= P_.N_pred;
  }
  S_.error_buffer[S_.err_pos_count] = S_.current_error_input;
  S_.err_pos_count += 1;
  if (S_.err_pos_count > V_.buffer_error_steps - 1)
  {  
    S_.err_pos_count = 0;
  }
  S_.error_counts = 0.0;
  long e_idx = 0;
  for ( e_idx = 0;
                   e_idx<(V_.buffer_error_steps - 1);
       e_idx += 1 )
  {
    if (S_.error_buffer[e_idx] != 0)
    {  
      S_.error_counts += S_.error_buffer[e_idx];
    }
  }
  if (S_.error_counts != 0)
  {  
    S_.error_rate = (1000 * S_.error_counts) / (V_.buffer_error_steps * P_.N_error);
    S_.fbk_rate = (1000 * S_.mean_fbk) / V_.buffer_steps;
    S_.w_fbk = std::abs(S_.error_rate) / std::max(std::max(std::abs(S_.error_rate), std::abs(S_.fbk_rate)), P_.C_error);
    S_.w_pred = 1 - S_.w_fbk;
  }
  else
  {  
    S_.w_fbk = 1;
    S_.w_pred = 0;
  }
  S_.in_rate = (1000.0 * ((S_.mean_pred * S_.w_pred + S_.mean_fbk * S_.w_fbk) / P_.buffer_size));
  S_.out_rate = P_.base_rate + P_.kp * S_.in_rate;
  S_.lambda_poisson = S_.out_rate * nest::Time::get_resolution().get_ms() * 0.001;
  S_.spike_count_out = ([&]() -> int { nest::poisson_distribution::param_type poisson_params(S_.lambda_poisson); int sample = poisson_dev_( nest::get_vp_specific_rng( get_thread() ), poisson_params); return sample; })();
  if (S_.spike_count_out > 0 && (S_.tick % V_.trial_steps) > V_.wait_steps)
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
void state_neuron::handle(nest::DataLoggingRequest& e)
{
  B_.logger_.handle(e);
}


void state_neuron::handle(nest::SpikeEvent &e)
{
#ifdef DEBUG
  std::cout << "[neuron " << this << "] state_neuron::handle(SpikeEvent)" << std::endl;
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
    if ( nestml_buffer_idx == state_neuron::PORT_NOT_AVAILABLE )
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

